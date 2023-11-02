import boto3
from datetime import datetime
import json
import urllib.parse


SOURCE_FRAME_BUCKET = 'image-uploads-bucket'
MODEL_DETECTED_FRAMES_BUCKET = "model-detected-fight-frames"
SNS_TOPIC_ARN = "arn:aws:sns:us-west-2:ACCOUNTNUMBERHERE:st-vrain-fight-notification"
DYNAMO_TABLE_NAME="st-vrain-window-db"
TEMP_DIRECTORY = '../tmp/'
IMAGE_MODEL_ARN = "arn:aws:rekognition:us-west-2:ACCOUNTNUMBERHERE:project/fight-detection"
MIN_CONFIDENCE = 1

s3_client = boto3.client('s3')
model_client = boto3.client('rekognition')
sns_client = boto3.client('sns')
dynamo_db = boto3.client('dynamodb')


def lambda_handler(event, context):
    file_name = urllib.parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"], encoding='utf-8')
    print(file_name)

    school, camera = get_school_camera(file_name)

    fight_detected = get_inference(file_name, SOURCE_FRAME_BUCKET)
    
    fight_detected = True
    fight_window = get_fight_window(school, camera)

    # Remove oldest entry from window
    fight_window.pop(0)

    if fight_detected:
        # If a fight was detected add a 1 to the window
        fight_window.append(1)

        # If we've met out fight detection threshold, send an alert
        # if sum(fight_window) == 3:
        #     publish_to_sns(file_name)
    else:
        # If a fight was not detected a 0 to the window
        fight_window.append(0)

    set_fight_window(school, camera, fight_window)


def get_school_camera(file_name):
    file_name = file_name.split("-")
    school = file_name[0]
    camera = file_name[1]

    return school, camera

def get_inference(file_name, bucket):
    response = model_client.detect_custom_labels(Image={'S3Object': {'Bucket': bucket, 'Name': file_name}},
                                                 MinConfidence=MIN_CONFIDENCE,
                                                 ProjectVersionArn=IMAGE_MODEL_ARN)
    labels = response['CustomLabels']
    for label in labels:
        if label["Name"] == "Fight" and label["Confidence"] > 10:
            return True
    return False


def publish_to_sns(detected_frame_name):
    url = create_presigned_url(MODEL_DETECTED_FRAMES_BUCKET, detected_frame_name)
    timestamp = datetime.now().strftime('%m-%d-%Y %H:%M:%S')
    sns_message= f"{timestamp}\n\nALERT: An active fight has been detected.\n\nPlease verify in the following image: {url}"
    sns_client.publish(TopicArn=SNS_TOPIC_ARN, Message=sns_message)


def create_presigned_url(bucket_name, object_name, expiration=3600):
    response = s3_client.generate_presigned_url('get_object',
                                                Params={'Bucket': bucket_name,
                                                        'Key': object_name},
                                                ExpiresIn=expiration)

    # The response contains the presigned URL
    return response


def get_fight_window(school_name, camera_name):
    dynamo_response = dynamo_db.get_item(
        TableName=DYNAMO_TABLE_NAME,
        Key={
            'School': {'S': school_name},
        }
    )


    window_as_string = dynamo_response["Item"]["Cameras"]["M"]["test_camera_1"]["S"]
    return json.loads(window_as_string)


def set_fight_window(school_name, camera_name, fight_window):
    dynamo_db.update_item(
        TableName=DYNAMO_TABLE_NAME,
        Key={ 'School': {'S': school_name} },
        UpdateExpression="set Cameras.#camera_name=:window",
        ExpressionAttributeNames={"#camera_name" : camera_name},
        ExpressionAttributeValues={":window" : {"S" : json.dumps(fight_window)}}
    )

