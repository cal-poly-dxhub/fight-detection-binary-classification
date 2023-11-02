import boto3
import cv2
from datetime import datetime


SOURCE_VIDEO_BUCKET = 'dxhub-svvsd-video-mp4'
OUTPUT_IMAGE_BUCKET = 'dxhub-svvsd-unlabeled-images'
MODEL_DETECTED_FRAMES_BUCKET = "model-detected-fight-frames"
SNS_TOPIC_ARN = "arn:aws:sns:us-west-2:ACCOUNTNUMBERHERE:fight-notification"
TEMP_DIRECTORY = '../tmp/'
IMAGE_MODEL_ARN = "arn:aws:rekognition:us-west-2:ACCOUNTNUMBERHERE:project/st-vrain-fight-detection-ratio-adjusted-1/version/st-vrain-fight-detection-ratio-adjusted-1.2022-05-01T14.51.16/1651441876871"
MIN_CONFIDENCE = 1

s3_client = boto3.client('s3')
model_client = boto3.client('rekognition')
sns_client = boto3.client('sns')


def get_inference(photo, bucket):
    response = model_client.detect_custom_labels(Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
                                                     MinConfidence=MIN_CONFIDENCE,
                                                     ProjectVersionArn=IMAGE_MODEL_ARN)
    print(response)
    labels = response['CustomLabels']
    for label in labels:
        if label["Name"] == "Fight" and label["Confidence"] > 10:
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

def main(event):
    file_name = event.file_name
    detected_frame_name = check_frames(file_name)

    if detected_frame_name:
        publish_to_sns(detected_frame_name)





