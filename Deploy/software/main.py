import threading
import requests
from requests.auth import HTTPDigestAuth
from datetime import datetime
import time
import csv
from torchvision import transforms
from torchvision import models
import torch
from PIL import Image
import torch.nn as nn
import numpy as np
import os
import io
import json
import traceback
import boto3
import random
from urllib.parse import urlparse

#import pullimage

# Camera URL
# hostname = "192.168.1.100"
# req_url = '/media/cam0/still.jpg?res=max'
#url = 'http://admin:admin@192.168.1.100/media/cam0/still.jpg?res=max'
#url = 'http://192.168.1.100/media/cam0/still.jpg?res=max'

# Username and password for digest authorization

CAMERA_URLS = "camera_endpoints.csv"
MODEL_PATH = "."
MODEL_DETECTED_FRAMES_BUCKET = "model-detected-fight-frames"
SNS_TOPIC_ARN = "arn:aws:sns:us-west-2:ACCOUNTNUMBERHERE:notification"
TEMP_DIRECTORY = "image_grab"
DYNAMO_TABLE_NAME="fight-detection-db"
FIGHT_THRESHHOLD = 0.15
FIGHTS_IN_A_ROW = 2
BASE_SMS_URL = "https://domain/tinyurl"
MAX_IMAGE_SIZE_FOR_INF = 512

# First release of pilot code at innovation center

session = boto3.Session(
    region_name='us-west-2'
)


s3_client = session.client('s3')
sns_client = session.client('sns')
dynamo_db = session.client('dynamodb')

def model_fn(model_dir):
    n_classes=2
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print('Loading the model.')
    model = models.resnet34(pretrained=True)

    n_features = model.fc.in_features
    model.fc = nn.Linear(n_features, n_classes)

    with open(os.path.join(model_dir, 'model.pth'), 'rb') as f:
        model.load_state_dict(torch.load(f,map_location=torch.device('cpu')))

    model.to(device).eval()
    #print('Done loading model')
    return model

def input_fn(image_data):
    try:
        image_data = Image.open(io.BytesIO(image_data))       
        image_data = image_data.convert('RGB')
        mode_to_nptype = {'I': np.int32, 'I;16': np.int16, 'F': np.float32}
        img = torch.from_numpy(
            np.array(image_data, mode_to_nptype.get(image_data.mode, np.uint8), copy=True)
        )
        # Use image size when doing inference
        inf_size = MAX_IMAGE_SIZE_FOR_INF
        if image_data.height < MAX_IMAGE_SIZE_FOR_INF:
            inf_size = image_data.height
        #print("INFERENCE SIZE:",inf_size)
        image_transform = transforms.Compose([
            transforms.CenterCrop(size=image_data.height),
            transforms.Resize(size=inf_size),
            transforms.ToTensor()
            #transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        return image_transform(image_data)

        raise Exception(f'Requested unsupported ContentType in content_type: {content_type}')
    except Exception as e:
        traceback.print_exc()
        print("Error", e)

def predict_fn(input_data, model):
    #print("TORCH",input_data.size(dim=1))
    # Use the torch.size class to determine the data frame size
    if torch.cuda.is_available():
        input_data = input_data.view(1, 3, input_data.size(dim=1), input_data.size(dim=1)).cuda()
    else:
        input_data = input_data.view(1, 3, input_data.size(dim=1), input_data.size(dim=1))
    with torch.no_grad():
        model.eval()
        out = model(input_data)
    return out

def update_dynamodb(school, ip, uuid, cam, url):
    dynamo_response = dynamo_db.update_item(
        TableName=DYNAMO_TABLE_NAME,
            Key={
                'school': {'S': school},
                'uuid': {'S': uuid}
            },
        UpdateExpression="SET PreSignedURL = :url, head = :cam, camera = :ip",
        ExpressionAttributeValues={
            ':url': {"S":url},
            ':cam': {"S":cam},
            ':ip': {"S":ip}
        },
        ReturnValues="UPDATED_NEW"
    )

def output_fn(prediction_output):
    class_names=['Fight', 'No Fight']    
    sm=nn.Softmax(dim=1)
    pred_out=sm(prediction_output)
    
    result = []
    
    pred={class_names[i]:f'{pred_out.cpu().numpy()[0][i]}' for i in range(len(class_names))}
    #print(f'Adding prediction: {pred}')
    result.append(pred)
    return (result)
def save_processed_tensor_image(tensor, filename):
    transform = transforms.ToPILImage()

    # convert the tensor to PIL image using above transform
    img = transform(tensor)
    #print(type(img))

# display the PIL image
    #img.show()
    img.save(filename)
def get_camera_ip_head_from_url(url):
    return_dict = {}
    # grab IP and camera number
    #http://192.168.1.100/media/cam0/still.jpg?res=max
    return_dict['ip'] = urlparse(url).netloc
    # figure out camer number
    return_dict['head'] = url[url.find('media')+6:url.find('media')+10]
    return return_dict

def save_temp_file(image_bytes, school, camera, head, prob):
    # catch FileNotFoundError: and make dir
    fight_image = Image.open(io.BytesIO(image_bytes))
    currentDateAndTime = datetime.now()
    currentTime = currentDateAndTime.strftime("%H-%M-%S.%f")
    
    directory = TEMP_DIRECTORY + '/' + school + '/' + camera + '/'+ head 
    file_name =  currentTime + "-" + prob + ".jpg"
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_return = os.path.join(directory, file_name)
    # print (file_return)
    # print (fight_image.height)
    # print (fight_image.width)
    # print (fight_image.format)
    # print (fight_image.size)
    fight_image.save(file_return)
    #print(file_return)
    return(file_return)

def publish_to_sns(detected_frame_name, school, ip, cam):
    url = create_presigned_url(MODEL_DETECTED_FRAMES_BUCKET, detected_frame_name)
    uuid = generate_uuid()
    update_dynamodb(school, ip, uuid, cam, url)
    url_query_parameters = BASE_SMS_URL + "?school=" + school + '&uuid=' + uuid
    timestamp = datetime.now().strftime('%m-%d-%Y %H:%M:%S')
    sns_message= f"{timestamp}\n\nALERT: An active fight has been detected.\n\nPlease verify in the following image: {url_query_parameters}"
    response = sns_client.publish(TopicArn=SNS_TOPIC_ARN, Message=sns_message)


def upload_to_model_detected_bucket(file_name, school, ip, cam):
    #print("FILENAME",file_name)
    # break key into folder/image
    bucket_key = school + "/" + ip + "/" + file_name[file_name.find("cam"):]
    #print("BUCKETKEY",bucket_key)
    s3_client.upload_file(file_name, MODEL_DETECTED_FRAMES_BUCKET, bucket_key)

    return bucket_key

def create_presigned_url(bucket_name, object_name, expiration=3600):
    response = s3_client.generate_presigned_url('get_object',
                                                Params={'Bucket': bucket_name,
                                                        'Key': object_name},
                                                ExpiresIn=expiration)

    # The response contains the presigned URL
    return response

def run_inference_on_url(model, school, url, username, password):
    # return the response from the URL read
    # Send a GET request to the URL with the authentication
    number_of_fights_detected = 0

    while True:
        #print("Checking:", url)
        response = requests.get(url,  auth=HTTPDigestAuth(username, password))
        # If the response status code is OK (200), save the image to a file
        if response.status_code == 200:
            processed_image = input_fn(response.content)
            output = predict_fn(processed_image, model)
            #save_processed_tensor_image(processed_image, "chris-small.jpg")
            result = output_fn(output)
            #print(type(result[0]["Fight"]))
            #print(type(processed_image))
            #print(result[0])\
            #ip_head = get_camera_ip_head_from_url(url)
            #save_temp_file(response.content, school, ip_head['ip'], ip_head['head'],result[0]["Fight"])
            currentDateAndTime = datetime.now()
            currentTime = currentDateAndTime.strftime("%H-%M-%S.%f")
            if float(result[0]["Fight"])>FIGHT_THRESHHOLD:
                ip_head = get_camera_ip_head_from_url(url)
                save_temp_file(response.content, school, ip_head['ip'], ip_head['head'],result[0]["Fight"])
                number_of_fights_detected += 1
                #print(number_of_fights_detected, result[0], currentDateAndTime)
            else:
                number_of_fights_detected = 0
                #print(number_of_fights_detected, result[0], currentDateAndTime)
        else:
            print(f'Failed to fetch image. Status code: {response.status_code}')
        
        # FIGHTS_IN_A_ROW has occured let's alert the autorities
        if number_of_fights_detected >= FIGHTS_IN_A_ROW:
            ip_head = get_camera_ip_head_from_url(url)
            file_to_upload =  save_temp_file(response.content, school, ip_head['ip'], ip_head['head'],result[0]["Fight"])
            #save_processed_tensor_image(processed_image, file_to_upload+"-small.jpg")
            detected_frame = upload_to_model_detected_bucket(file_to_upload, school, ip_head['ip'], ip_head['head'])
            publish_to_sns(detected_frame, school, ip_head['ip'], ip_head['head'])
            # delete local file
            number_of_fights_detected = 0
            #print("Gotcha!")
            time.sleep(3)
        time.sleep(0.5)


def generate_uuid():
    raw_uuid = '{:032x}'.format(random.getrandbits(128))
    return '{}-{}-4{}-{}{}-{}'.format(
        raw_uuid[:8], 
        raw_uuid[8:12], 
        raw_uuid[13:16], 
        hex(8 + random.getrandbits(3) % 4)[2:], 
        raw_uuid[16:18], 
        raw_uuid[18:]
    )


def main():
    # load model
    model = model_fn(MODEL_PATH)

    # Read the config file with URLs and passwords
    # url,username,password
    with open(CAMERA_URLS, 'r') as csvfile:
    # Create a CSV reader object
        reader = csv.reader(csvfile)
        # Create a thread for each URL
        threads = []
        for row in reader:
            school, url, username, password = row
            print("Opening thread to camera: ",url)
            thread = threading.Thread(target=run_inference_on_url, args=(model, school, url, username, password))
            threads.append(thread)
            thread.start()
        #TODO wht if a thread fails
        # Wait for all threads to complete
        # check status of each thrad vriable shared with parent thread share data 
        for thread in threads:
            thread.join()

if __name__ == '__main__':
    main()
