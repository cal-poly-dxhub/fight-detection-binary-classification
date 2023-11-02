import boto3
import cv2
from datetime import datetime
import glob
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import csv
import os

from torchvision import transforms
from torchvision import models  
import torch
import torch.nn as nn
import numpy as np
import os
import io
import json
import traceback

SOURCE_VIDEO_BUCKET = 'video-mp4'
OUTPUT_IMAGE_BUCKET = 'unlabeled-images'
MODEL_DETECTED_FRAMES_BUCKET = "model-detected-fight-frames"
SNS_TOPIC_ARN = "arn:aws:sns:us-west-2:ACCOUNTNUMBERHERE:fight-notification"
TEMP_DIRECTORY = '/images-for-training/test/Fight'
IMAGE_MODEL_ARN = "arn:aws:rekognition:us-west-2:ACCOUNTNUMBERHERE:project/fight-detection-1"
MIN_CONFIDENCE = 1
DYNAMO_TABLE_NAME="fight-detection-db"
CONFIDENCE_LEVEL=20
MODEL_PATH = "/deploy/software"
MAX_IMAGE_SIZE_FOR_INF = 288

session = boto3.Session(
    region_name='us-west-2'
)

s3_client = session.client('s3')
model_client = session.client('rekognition')
sns_client = session.client('sns')
dynamo_db = session.client('dynamodb')


def get_inference(photo, bucket):
    response = model_client.detect_custom_labels(Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
                                                     MinConfidence=MIN_CONFIDENCE,
                                                     ProjectVersionArn=IMAGE_MODEL_ARN)
    print(response)
    labels = response['CustomLabels']
    for label in labels:
        if label["Name"] == "Fight" and label["Confidence"] > CONFIDENCE_LEVEL :
            return True
    return False


def check_frames(file_name):
    """
    Split video in ../data/video into frames saved to ../data/imgs
    """

    # Read the video from specified path
    cam = cv2.VideoCapture(TEMP_DIRECTORY + file_name)

    current_frame = 0

    target_frame = 0

    fps = cam.get(cv2.CAP_PROP_FPS)
    frame_increment = int(fps / 2)

    num_frame = 0

    window_size = 6

    detection_window = [0] * window_size

    while True:
        ret, frame = cam.read()

        if not ret:
            break

        if current_frame == target_frame:
            frame_name = file_name.replace(".mp4", "") + '_frame_' + str(current_frame) + '.jpg'
            print("Analyzing " + frame_name + "...")
            cv2.imwrite(TEMP_DIRECTORY + frame_name, frame)
            target_frame += frame_increment


            fight_detected = get_inference(TEMP_DIRECTORY + frame_name)

            window_index = num_frame % window_size
            if fight_detected:
                detection_window[window_index] = 1
            else:
                detection_window[window_index] = 0

            if sum(detection_window) == 3:
                detected_frame_name = upload_to_model_detected_bucket(frame_name)
                return detected_frame_name

            num_frame += 1

        current_frame += 1

    # Release all space and windows once done
    cam.release()
    cv2.destroyAllWindows()

    return False

def get_fight_window(school_name, camera_name):
    print(school_name, camera_name)
    dynamo_response = dynamo_db.get_item(
        TableName=DYNAMO_TABLE_NAME,
        Key={
            'School': {'S': school_name},
            'Camera': {'S': camera_name}
        }
    )
def update_fight_window(school_name, camera_name, fight_detected):
    print(school_name, camera_name)
    # Check existing value
    dynamo_response = dynamo_db.get_item(
        TableName=DYNAMO_TABLE_NAME,
        Key={
                'School': {'S': school_name},
                'Camera': {'S': camera_name}
        }
    )
    current_fight_count = int(dynamo_response["Item"]["FightInARow"]['N'])
    print(type(current_fight_count))
    
    if(fight_detected):
        current_fight_count += 1
    else:
        current_fight_count = 0
    
    dynamo_response = dynamo_db.update_item(
        TableName=DYNAMO_TABLE_NAME,
            Key={
                'School': {'S': school_name},
                'Camera': {'S': camera_name}
            },
        UpdateExpression="SET FightInARow = :fights",
        ExpressionAttributeValues={
            ':fights': {"N":str(current_fight_count)}
        },
        ReturnValues="UPDATED_NEW"
    )
    print(dynamo_response)

def publish_to_sns(detected_frame_name):
    url = create_presigned_url(MODEL_DETECTED_FRAMES_BUCKET, detected_frame_name)
    timestamp = datetime.now().strftime('%m-%d-%Y %H:%M:%S')
    sns_message= f"{timestamp}\n\nALERT: An active fight has been detected.\n\nPlease verify in the following image: {url}"
    response = sns_client.publish(TopicArn=SNS_TOPIC_ARN, Message=sns_message)


def upload_to_model_detected_bucket(frame_name):
    timestamp = datetime.now().strftime("--%m-%d-%Y--%H:%M:%S.jpg")
    detected_frame_name = frame_name.split(".jpg")[0] + timestamp
    s3_client.upload_file(TEMP_DIRECTORY + frame_name, MODEL_DETECTED_FRAMES_BUCKET, detected_frame_name)

    return detected_frame_name

def create_presigned_url(bucket_name, object_name, expiration=3600):
    response = s3_client.generate_presigned_url('get_object',
                                                Params={'Bucket': bucket_name,
                                                        'Key': object_name},
                                                ExpiresIn=expiration)

    # The response contains the presigned URL
    return response

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
    print('Done loading model')
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
        # image_transform = transforms.Compose([
        #     transforms.CenterCrop(size=512),
        #     transforms.Resize(size=512),
        #     transforms.ToTensor()
        #     #transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        # ])
        return image_transform(image_data)

        raise Exception(f'Requested unsupported ContentType in content_type: {content_type}')
    except Exception as e:
        traceback.print_exc()
        print("something is wrong", e)

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

def output_fn(prediction_output):
    class_names=['Fight', 'No Fight']    
    sm=nn.Softmax(dim=1)
    pred_out=sm(prediction_output)
    
    result = []
    
    pred={class_names[i]:f'{pred_out.cpu().numpy()[0][i]}' for i in range(len(class_names))}
    #print(f'Adding prediction: {pred}')
    result.append(pred)
    return (result)

def detect_custom_labels_local_file(photo):
    retval = []
    # switch this to {'Fight': '0.7068127393722534', 'No Fight': '0.2931872606277466'}
    with open(photo, 'rb') as image:
        response = model_client.detect_custom_labels(Image={'Bytes': image.read()},
                                                MinConfidence=MIN_CONFIDENCE,
                                                ProjectVersionArn=IMAGE_MODEL_ARN)
    print("DEKKKK",response)
    #{'CustomLabels': [{'Name': 'No Fight', 'Confidence': 71.5260009765625}, {'Name': 'Fight', 'Confidence': 28.474000930786133}], 'ResponseMetadata': {'RequestId': '2be23fdd-8b48-4a42-a18b-30fe8ba12d9c', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': '2be23fdd-8b48-4a42-a18b-30fe8ba12d9c', 'content-type': 'application/x-amz-json-1.1', 'content-length': '117', 'date': 'Thu, 11 May 2023 16:56:26 GMT'}, 'RetryAttempts': 0}}    
    labels = response['CustomLabels']
    classification = {}
    for label in response['CustomLabels']:
        classification = {}
        classification[label['Name']]=label['Confidence']
        retval.append(classification)
        # if label['Name'] == 'Fight' and label['Confidence']>CONFIDENCE_LEVEL:
        #     print (photo, '->', label['Name'] + ' : ' + str(label['Confidence']))
        #     #retval = (True,label['Confidence'])
    print(retval)
    return retval #len(response['CustomLabels'])

def detect_labels_local_file(photo):
    with open(photo, 'rb') as image:
        response = model_client.detect_labels(Image={'Bytes': image.read()})
        
    print('Detected labels in ' + photo)    
    for label in response['Labels']:
        print (label['Name'] + ' : ' + str(label['Confidence']))

    return len(response['Labels'])


    # print('Detected labels in ' + photo)    
    # for label in response['Labels']:
    #     print (label['Name'] + ' : ' + str(label['Confidence']))

    # return len(response['Labels'])

def detect_custom_model_local_file(model, file):
    with open(file, 'rb') as image:
        processed_image = input_fn(image.read())
        output = predict_fn(processed_image, model)
        result = output_fn(output)
        #print(type(result[0]["Fight"]))
        #print(type(processed_image))
        print(result[0])
        return result

def label_image(f, text):
    image_font = ImageFont.truetype("DejaVuSansMono.ttf", 30)
    image = Image.open(f)
        
    draw = ImageDraw.Draw(image)
    draw.text((155, 155 ), text, font=image_font, fill =(255, 0, 0))
    image.show()
    #image.save(f)



def main():
     # load model
    model = model_fn(MODEL_PATH)

    fight_count = 0
    print(os.getcwd())
    files_to_process = glob.glob(TEMP_DIRECTORY+"/*.jpg")
    #print(files_to_process)
    for f in files_to_process:
    # with open('images-2.csv') as csv_file:
    #     csv_reader = csv.reader(csv_file, delimiter=',')
    #     counter = 0
    #     for f in csv_reader:
            print("DEK", f)
            #result = detect_custom_labels_local_file(f)
            result = detect_custom_model_local_file(model, f)
            #print("DEK",result)
            label_image(f, "CUSTOM\n" + str(result))
            # if result[0]:
            #     fight_count += 1
            #     label_image(f, + str(result))
            # else:
            #     fight_count = 0
            #     label_image(f, 'NO FIGHT')
            # print(fight_count)
            # if fight_count >= 3:
            #     print ('FIGHT FIGHT FIGHT')
    #update_fight_window('Erie_High','Main_Bldg_West_Hallway', True)

        
    


if __name__ == '__main__':
    main()