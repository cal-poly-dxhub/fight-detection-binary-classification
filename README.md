# Overall Structure of the Repository

### This project was divided into 5 pieces

**--Each of these folders contains their own README's with greater detail--**

1. Data Cleaning (./DataCleaning)
    * Convert, split, and clean video
2. Model Training / Inference (./Model)
    * Start, stop, use, train model
3. Infrastructure (./Infrastructure)
    * Cdk project to spin up lambda, dynamo, s3
4. Camera Utilities (./camera)
    * These are utlities to interface with cameras through RTSP
5. Deploy (.deploy)
    * This was the code that was deployed for the PoC


**ULTIMATELY, PRODUCTION ONLY NEEDS THE CDK STACK (./INFRASTRUCTURE) CONTAINING CODE**
**TO SPINUP PRODUCTION RESOURCES AND INFERENCE CODE**

This project has a variety of utilities to split MP4 video into images and use those images to 
train a vision model around binary classification of labeled images.  The Model/CustomModel has a 
notebook for training using transfer learning on top of Resnet34.

Everything else were necesary pieces along the way and will be helpful in future iterations


## Python Versioning + Lambda 
Lambda will have a Python 3.7.4 runtime and so it is important to be careful with
python packages. 
* Create venv:```python3.7 -m venv .venv```
* Activate venv:```source .venv/bin/activate```
* Install packages from requirements.txt:```pip install -r requirements.txt```

## Data Directory Structure
Currently, the project expects /data/video, /data/imgs, and /data/output directories
on the same level as /src

## Cameras
Axis P3367-VE 5mp Dome (Slowly phasing out)
Avigilon 9/12W-H3-3MH-DP1/DC1 Multi-Head
https://assets.avigilon.com/file_library/pdf/h3-multisensor/avigilon-h3-multisensor-datasheet-en-rev5.pdf

Avigilon 15/20C-H4A-3/4MH-180/270 Multi-Head
https://assets.avigilon.com/file_library/pdf/h4-multisensor/avigilon-h4m-mh-datasheet-en-rev9.pdf

Avigilon 4.0/5.0-H5A-DC1 Dome
https://assets.avigilon.com/file_library/pdf/h5a/avigilon-h5a-line-camera-datasheet-en-rev15.pdf

Software:
Avigilon Access Control Center Server/Client

Version:
7.12.0.30 - Upgrading to 7.14.2.8

https://www.avigilon.com/products/cameras-sensors/mh

## Video Formats
https://www.adobe.com/creativecloud/video/discover/best-video-format.html

## Homebrew
```brew install ffmpeg```



