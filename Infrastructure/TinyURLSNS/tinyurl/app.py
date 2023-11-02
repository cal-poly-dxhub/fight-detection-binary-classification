import json
import boto3

DYNAMO_TABLE_NAME="st-vrain-fight-detection-db"
dynamo_db = boto3.client('dynamodb')

def lambda_handler(event, context):
    print(event)
    redirectTo="https://dxhub.calpoly.edu/image-retrieved/"
    try:
        if event['queryStringParameters']!= None:
            school_name = event['queryStringParameters']['school']
            camera_uuid = event['queryStringParameters']['uuid']

            # Check existing value
            print("TESTING", school_name, camera_uuid)
            dynamo_response = dynamo_db.get_item(
                TableName=DYNAMO_TABLE_NAME,
                Key={
                        'school': {'S': school_name},
                        'uuid': {'S': camera_uuid}
                }
            )
            redirectTo = dynamo_response["Item"]["PreSignedURL"]['S']
            if len(redirectTo) == 0:
                redirectTo = 'https://dxhub.calpoly.edu/image-retrieved/'
    except KeyError:
       redirectTo = 'https://dxhub.calpoly.edu/image-retrieved/'
    except TypeError:
       redirectTo = 'https://dxhub.calpoly.edu/image-retrieved/'

    # no presigned URL set
    
    # remove re-direct URL from DynamoDB
    # dynamo_response = dynamo_db.update_item(
    #     TableName=DYNAMO_TABLE_NAME,
    #         Key={
    #             'School': {'S': school_name},
    #             'Camera': {'S': cameraip_head}
    #         },
    #     UpdateExpression="SET PreSignedURL = :url",
    #     ExpressionAttributeValues={
    #         ':url': {"S":'https://dxhub.calpoly.edu/image-retrieved/'}
    #     },
    #     ReturnValues="UPDATED_NEW"
    # )

    return {
        "statusCode": 302,
        "headers": {
            "Location": redirectTo,
        }
    }
