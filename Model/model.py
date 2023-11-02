

import time
from PIL import Image, ImageDraw, ExifTags, ImageColor, ImageFont
import io
import boto3
import base64

session = boto3.Session(profile_name='PROFILE')
model_client = session.client('rekognition')

def start_model(project_arn, model_arn, version_name, min_inference_units):

    try:
        # Start the model
        print('Starting model: ' + model_arn)
        response = model_client.start_project_version(
            ProjectVersionArn=model_arn, MinInferenceUnits=min_inference_units)
        # Wait for the model to be in the running state
        project_version_running_waiter = model_client.get_waiter(
            'project_version_running')
        project_version_running_waiter.wait(
            ProjectArn=project_arn, VersionNames=[version_name])

        #Get the running status
        describe_response = model_client.describe_project_versions(ProjectArn=project_arn,
                                                             VersionNames=[version_name])
        for model in describe_response['ProjectVersionDescriptions']:
            print("Status: " + model['Status'])
            print("Message: " + model['StatusMessage'])
    except Exception as e:
        print(e)

    print('Done...')


def display_image(photo, response, bucket=None):

    if bucket:
        # Load image from S3 bucket
        s3_connection = boto3.resource('s3')

        s3_object = s3_connection.Object(bucket, photo)
        s3_response = s3_object.get()

        stream = io.BytesIO(s3_response['Body'].read())
    else:
        image = open(photo, 'rb')
        stream = io.BytesIO(image.read())

    image = Image.open(stream)

    # Ready image to draw bounding boxes on it.
    imgWidth, imgHeight = image.size
    draw = ImageDraw.Draw(image)

    # calculate and display bounding boxes for each detected custom label
    print('Detected custom labels for ' + photo)
    for customLabel in response['CustomLabels']:
        print('Label ' + str(customLabel['Name']))
        print('Confidence ' + str(customLabel['Confidence']))
        if 'Geometry' in customLabel:
            box = customLabel['Geometry']['BoundingBox']
            left = imgWidth * box['Left']
            top = imgHeight * box['Top']
            width = imgWidth * box['Width']
            height = imgHeight * box['Height']

            fnt = ImageFont.truetype('/Library/Fonts/Arial.ttf', 50)
            draw.text(
                (left, top), customLabel['Name'], fill='#00d400', font=fnt)

            print('Left: ' + '{0:.0f}'.format(left))
            print('Top: ' + '{0:.0f}'.format(top))
            print('Label Width: ' + "{0:.0f}".format(width))
            print('Label Height: ' + "{0:.0f}".format(height))

            points = (
                (left, top),
                (left + width, top),
                (left + width, top + height),
                (left, top + height),
                (left, top))
            draw.line(points, fill='#00d400', width=5)

    image.show()


def show_custom_labels(model, photo, min_confidence, bucket=None,):
  

    #Call DetectCustomLabels
    if bucket is not None:
        response = model_client.detect_custom_labels(Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
                                           MinConfidence=min_confidence,
                                           ProjectVersionArn=model)

    # For object detection use case, uncomment below code to display image.
    else:
        image = open(photo, 'rb')
        image_bytes = image.read()
        response = model_client.detect_custom_labels(Image={"Bytes" : image_bytes},
                                    MinConfidence=min_confidence,
                                    ProjectVersionArn=model)

    print("response: ", response)
    display_image(photo,response)

    return len(response['CustomLabels'])


def stop_model(model_arn):

    print('Stopping model:' + model_arn)

    #Stop the model
    try:
        response = model_client.stop_project_version(ProjectVersionArn=model_arn)
        status = response['Status']
        print('Status: ' + status)
    except Exception as e:
        print(e)

    print('Done...')

def main():
    project_arn = 'arn:aws:rekognition:us-west-2:ACCOUNTNUMBERHERE:project/fight-detection'
    model_arn = 'arn:aws:rekognition:us-west-2:ACCOUNTNUMBERHERE:project/fight-detection'
    # bucket = 'MY_BUCKET'
    # photo = 'MY_IMAGE_KEY'
    model = 'arn:aws:rekognition:us-west-2:ACCOUNTNUMBERHERE:project/fight-detection'

    # start the model
    min_inference_units = 1
    version_name = 'fight-detection'
    start_model(project_arn, model_arn, version_name, min_inference_units)


    # use model
    min_confidence = 95
    photo = "./fight2.jpg"
    label_count = show_custom_labels(model,photo,min_confidence)
    print("Custom labels detected: " + str(label_count))

    # stop model
    # stop_model(model_arn)


if __name__ == "__main__":
    main()
