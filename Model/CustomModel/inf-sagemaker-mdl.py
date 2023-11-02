# This file was used to run local inference on a trained model using PyTorch
# Requirements:
# 1) directory of images you'd like to run inference on
# 2) saved model file model.pth
from datetime import datetime
import glob
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import json
import os
import torch
import numpy as np
import requests
from torchvision import transforms
from torchvision import models
from torchvision.utils import save_image
import torch.nn as nn
import io
import traceback
import time

SOURCE_IMAGE_PATH = '../temp-images'
MODEL_PATH = "Model/saved-model"
SNS_TOPIC_ARN = "arn:aws:sns:us-west-2:ACCOUNTNUMBERHERE:fight-notification"
TEMP_DIRECTORY = '../tmp/'
MIN_CONFIDENCE = 1
TEMP_DIRECTORY = './tmp/'
CONFIDENCE_LEVEL=50


def model_fn(model_dir):
  #  print('Loading... ',os.getcwd())
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

def input_fn(image_data, content_type='application/x-image'):
  #  print('Deserializing the input data.')
    try:
        if content_type == 'application/x-image':
            image_data = Image.open(io.open(image_data, 'rb'))          
            image_data = image_data.convert('RGB')
            mode_to_nptype = {'I': np.int32, 'I;16': np.int16, 'F': np.float32}
            img = torch.from_numpy(
                np.array(image_data, mode_to_nptype.get(image_data.mode, np.uint8), copy=True)
            )
            image_transform = transforms.Compose([
                transforms.Resize(size=512),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])
     #       print('Done deserializing the input data.')
            return image_transform(image_data)

        raise Exception(f'Requested unsupported ContentType in content_type: {content_type}')
    except Exception as e:
        traceback.print_exc()
        print("something is wrong", e)

def predict_fn(input_data, model):
    #print('Generating prediction based on input parameters.')
    if torch.cuda.is_available():
        print(input_data.size())
        input_data = input_data.view(1, 3, 512, 512).cuda()
    else:
        print(input_data.size())
        input_data = input_data.view(1, 3, 512, 1365)
    with torch.no_grad():
        model.eval()
        out = model(input_data)
    return out

def output_fn(prediction_output, accept='application/json'):
    #print('Serializing the generated output.')
    class_names=['Fight', 'No Fight']    
    sm=nn.Softmax(dim=1)
    pred_out=sm(prediction_output)
    
    result = []
    
    pred={class_names[i]:f'{pred_out.cpu().numpy()[0][i]}' for i in range(len(class_names))}
    #print(f'Adding prediction: {pred}')
    result.append(pred)

    if accept == 'application/json':
        return json.dumps(result), accept
    raise Exception(f'Requested unsupported ContentType in Accept: {accept}')




# def publish_to_sns(detected_frame_name):
#     url = create_presigned_url(MODEL_DETECTED_FRAMES_BUCKET, detected_frame_name)
#     timestamp = datetime.now().strftime('%m-%d-%Y %H:%M:%S')
#     sns_message= f"{timestamp}\n\nALERT: An active fight has been detected.\n\nPlease verify in the following image: {url}"
#     response = sns_client.publish(TopicArn=SNS_TOPIC_ARN, Message=sns_message)



# def create_presigned_url(bucket_name, object_name, expiration=3600):
#     response = s3_client.generate_presigned_url('get_object',
#                                                 Params={'Bucket': bucket_name,
#                                                         'Key': object_name},
#                                                 ExpiresIn=expiration)

#     # The response contains the presigned URL
#     return response


def label_image(f, text):
    image_font = ImageFont.truetype("DejaVuSansMono.ttf", 64)
    image = Image.open(f)
        
    draw = ImageDraw.Draw(image)
    draw.text((1000, 750 ), text, font=image_font, fill =(255, 0, 0))
    image.show()
    #image.save(f)



def main():
    # load model
    model = model_fn(MODEL_PATH)

    files_to_process = glob.glob(SOURCE_IMAGE_PATH+"/*.jpg")
    count=0
    st = time.time()
    for image_file in files_to_process:
        #print(image_file)
        processed_image = input_fn(image_file)
        # evalute size of shruken image
        save_image(processed_image, SOURCE_IMAGE_PATH+str(count)+'-sample_downsize.jpg')
        # print(type())processed_image
        # sample = Image.open(io.open(processed_image, 'rb'))
        # sample.save(SOURCE_IMAGE_PATH+'sample_downsize.jpg')
        output = predict_fn(processed_image, model)
        print (output_fn(output))
        count+=1
        if count > 50:
            break
    et = time.time()
    print ("Processed ",count, " images in ", et-st, " using cuda ",torch.cuda.is_available())
    # fight_count = 0
    # with open('images-2.csv') as csv_file:
    #     csv_reader = csv.reader(csv_file, delimiter=',')
    #     counter = 0
    #     for f in csv_reader:
    #         image_file = TEMP_DIRECTORY + f[0]
    #         result = detect_custom_labels_local_file(image_file)
    #         if result[0]:
    #             fight_count += 1
    #             label_image(image_file, 'FIGHT\n'+str(result[1]))
    #         else:
    #             fight_count = 0
    #             label_image(image_file, 'NO FIGHT')
    #         print(fight_count)
    #         if fight_count >= 3:
    #             print ('FIGHT FIGHT FIGHT')
    #         counter += 1
    #update_fight_window('Erie_High','Main_Bldg_West_Hallway', True)

        
    


if __name__ == "__main__":
    main()