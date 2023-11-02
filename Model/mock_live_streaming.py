import cv2
import boto3
from datetime import datetime
import time
import os
import csv

# the max number of frames we want to capture regardless of camera FPS
FRAME_PER_SECOND_MAX = 2
IMAGE_MODEL_ARN = "arn:aws:rekognition:us-west-2:ACCOUNTNUMBERHERE:CUSTOMLABLESMODEL"
MIN_CONFIDENCE = 1
TEMP_DIRECTORY = './tmp/'

session = boto3.Session(profile_name='PROFILE')
s3_client = session.client('s3')
model_client = session.client('rekognition')

def write_csv_record(rows):
    images_file = open('images.csv', 'w', newline='\n')
    images_writer = csv.writer(images_file)
    for row in rows:
        print(row)
        images_writer.writerow([row])
    
    images_file.close()
def detect_custom_labels_local_file(photo):
    retval = False
    with open(photo, 'rb') as image:
        response = model_client.detect_custom_labels(Image={'Bytes': image.read()},
                                                MinConfidence=MIN_CONFIDENCE,
                                                ProjectVersionArn=IMAGE_MODEL_ARN)
    #print(response)    
    labels = response['CustomLabels']
    for label in response['CustomLabels']:
        if label['Name'] == 'Fight' and label['Confidence']>50:
            print (photo, '->', label['Name'] + ' : ' + str(label['Confidence']))
            retval = True
    return retval #len(response['CustomLabels'])

def upload_frames(file_name):
    print("Starting")
    #print(os.getcwd())
    # Read the video from specified path
    cam = cv2.VideoCapture(TEMP_DIRECTORY + file_name)
    
    # with so many FPS we want to only upload frames 2 FPS max
    # frame we are currently processing
    current_frame = 0
    # frame we want to upload
    target_frame = 0

    fps = cam.get(cv2.CAP_PROP_FPS)
    print("FPS=", fps)
    #
    capture_every_x_frame = int(fps / FRAME_PER_SECOND_MAX)

    num_frames = 0
    extracted_frame = 0
    fight_count = 0
    image_files = []
    while True:
       
        ret, frame = cam.read()
        if not ret:
            break
        
        if current_frame == target_frame:
            frame_name =  'Erie_High-Main_Bldg_West_Hallway-' + str(extracted_frame)  + '.jpg'
            fight_image = TEMP_DIRECTORY + frame_name
            #start = datetime.now()
            cv2.imwrite(fight_image, frame)
            image_files.append(frame_name)
            #print("Write image took ", datetime.now()-start)
            print(fight_image)
            
            # if detect_custom_labels_local_file(fight_image):
            #     fight_count += 1
            # else:
            #     fight_count = 0
           
            # if fight_count >= 3:
            #     print ('FIGHT FIGHT FIGHT->',fight_image)
            #     break
            target_frame += capture_every_x_frame
            extracted_frame +=1
            #start = datetime.now()
            #s3_client.upload_file(fight_image, "st-vrain-inference-images-upload", frame_name)
            #print("S3 upload took ", datetime.now()-start)
        num_frames += 1
        current_frame += 1
        # if current_frame == 40:
        #     break        
    #write_csv_record(image_files)
    # Release all space and windows once done
    cam.release()
    cv2.destroyAllWindows()


def stress_test(frames):
    for frame_name in frames:
        print(datetime.now())
        s3_client.upload_file(TEMP_DIRECTORY + frame_name, "st-vrain-inference-images-upload", frame_name)


frames = [
    "test_school-test_1.jpg",
    "test_school-test_0.jpg",
    "test_school-test_5.jpg",
    "test_school-test_2.jpg",
    "test_school-test_6.jpg",
    "test_school-test_3.jpg",
    "test_school-test_4.jpg"
]

upload_frames("Fight.mp4")
#stress_test(frames)
