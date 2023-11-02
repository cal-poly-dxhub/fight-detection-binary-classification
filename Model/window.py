import boto3
import cv2
import model
import os
from datetime import datetime
import logging
from botocore.exceptions import ClientError


LOCAL_RUN = True

if LOCAL_RUN: 
    session = boto3.Session(profile_name='PROFILE')
    s3_client = session.client('s3')
    s3 = session.resource('s3')
    sns_client = session.client('sns')
else:
    print("NOT SET UP FOR ECS YET")

SOURCE_VIDEO_BUCKET = 'video-mp4'
OUTPUT_IMAGE_BUCKET = 'unlabeled-images'
MODEL_DETECTED_FRAMES_BUCKET = "fight-frames"
SNS_TOPIC_ARN = "arn:aws:sns:us-west-2:ACCOUNTNUMBERHERE:fight-notification"
TEMP_DIRECTORY = '../tmp/'


def detect_fight(file_name):
    try:
        # print("Downloading " + file_name)
        # s3_client.download_file(Bucket=SOURCE_VIDEO_BUCKET,
        #                         Key=file_name,
        #                         Filename=TEMP_DIRECTORY + file_name)
        print("Checking for fights...")
        fight_detected = check_frames(file_name)

        if fight_detected:
            print("Fight Detected")

        else:
            print("Fight Not Detected")

    except Exception as e:
        print("An exception occurred: {}".format(e))

def upload_to_model_detected_bucket(frame_name):
    timestamp = datetime.now().strftime("--%m-%d-%Y--%H:%M:%S.jpg")
    detected_frame_name = frame_name.split(".jpg")[0] + timestamp
    s3_client.upload_file(TEMP_DIRECTORY + frame_name, MODEL_DETECTED_FRAMES_BUCKET, detected_frame_name)

    return detected_frame_name

def create_presigned_url(bucket_name, object_name, expiration=3600):
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response

def publish_to_sns(detected_frame_name):
    url = create_presigned_url(MODEL_DETECTED_FRAMES_BUCKET, detected_frame_name)
    timestamp = datetime.now().strftime('%m-%d-%Y %H:%M:%S')
    sns_message= f"{timestamp}\n\nALERT: An active fight has been detected.\n\nPlease verify in the following image: {url}"
    response = sns_client.publish(TopicArn=SNS_TOPIC_ARN, Message=sns_message)


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


            fight_detected = model.run_model(TEMP_DIRECTORY + frame_name)

            window_index = num_frame % window_size
            if fight_detected:
                detection_window[window_index] = 1
            else:
                detection_window[window_index] = 0

            if sum(detection_window) == 3:
                detected_frame_name = upload_to_model_detected_bucket(frame_name)
                publish_to_sns(detected_frame_name)

                return True

            num_frame += 1

        current_frame += 1

    # Release all space and windows once done
    cam.release()
    cv2.destroyAllWindows()

    return False


def main():

    # hallway
    # detect_fight("Fight_20---000.mp4")

    # girls in stairwell
    # detect_fight("Fight_15_trimmed---001.mp4")

    # perfect fight
    # detect_fight("Fight_4---000.mp4")

    # empty cafeteria 
    detect_fight("Fight_24---000.mp4")

main()
