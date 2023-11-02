import boto3
import json
import os


MANIFEST_FILE = 'DataCleaning/testing_manifest_with_validation.json'
INPUT_IMAGE_BUCKET  = 'unlabeled-images'
OUTPUT_IMAGE_BUCKET = 'labeled-images'
OUTPUT_IMAGE_PATH = 'images-for-training/testing/'


def main(): 
    s3 = boto3.client('s3')

    #split training data into train and validation for pytorch ML model
    file = open(MANIFEST_FILE, 'r')
    lines = file.readlines()
    # Go through each line grab json object push into list
    # GOAL: break training into 80/20
    data = {}
    i=0
    for index, line in enumerate(lines):
        i+=1
        #print("Line {}: {}".format(index, line.strip()))
        data = json.loads(line)
        label = data["labeling4-clone-metadata"]["class-name"]
        # grab key
        s3_file = data["source-ref"].rpartition('/')[-1]
        print("Downloading ", s3_file)
        s3.download_file(INPUT_IMAGE_BUCKET, s3_file , OUTPUT_IMAGE_PATH + "/"+ label + "/" + s3_file)

    

    file.close()
    

main()