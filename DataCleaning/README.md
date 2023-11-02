# DataCleaning

All code and directories part of AVI -> mp4 conversion pipeline


## **Files / Folders**

### **src/main.py:** 
This is the code that gets dockerized and run through ECS and Evenbridge rule each time 
video is uploaded to avi bucket

1. Determines which files need to be converted (avi format)
2. Downloads files
3. Converts avi -> mp4 
    3a. Uploads mp4 to 'video-mp4'
4. Splits mp4 into into jpgs 
    
    4a. Uploads every 10th frame to 'unlabeled-images' for labeling
5. Removes original avi video from 'video-avi'

### **Notes**
* Can run locally or in ECS using LOCAL_RUN flag
* Expects Directory with ./tmp, ./source_videos folders (see macros at top of file if confusion)
* If running locally, must have AWS profile setup named PROFILn
* Any AVI video longer than 240 seconds will be split into 2 minute clips

### **scratch:**
* convert_images.py: scratch copy of main.py
* split_video_local.py: file to run avi -> mp4, split mp4 -> jpg locally
    * CONTAINS REMOVE DEAD FRAMES ALGORITHM
* split_video.py: scratch copy of split_video_local.py/main.py designed to run in ECS



### **Docker and ECR**
Note: 
* Used in the current iteration of main.py (file used for Event Bridge ECS Task conversion) are folders ./tmp, ./source_videos, ./src
* Uses requirements_only_main.txt which contains only the required python libraries
in order to create the smallest Docker Image possible

**To create Docker Image and upload to ECR...**


1. Login: 

    ```
    aws ecr-public get-login-password --region us-east-1  | docker login --username AWS --password-stdin public.ecr.aws/
    ```

2. Build Image: 
    ```
    docker build -t conversion .
    ```

3. Tag Image:
    ```
    docker tag conversion:latest public.ecr.aws/m50v4y3/conversion:latest
    ```

4. Push Image: 
    ```
    docker push public.ecr.aws//conversion:latest 
    ```

5. To Run Image Locally: 
    ```
    docker run conversion:latest
    ```

6. To inspect filesystem while running:
    ```
    docker exec -it hardcore_elbakyan  /bin/bash

    ```
