# Collaboration

Thanks for your interest in our solution. Having specific examples of replication and usage allows us to continue to grow and scale our work. If you clone or use this repository, kindly shoot us a quick email to let us know you are interested in this work!

<wwps-cic@amazon.com>

# Disclaimers

**Customers are responsible for making their own independent assessment of the information in this document.**

**This document:**


Customers are responsible for making their own independent assessment of the information in this document. 

This document: 

(a) is for informational purposes only, 

(b) references AWS product offerings and practices, which are subject to change without notice, 

(c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS products or services are provided “as is” without warranties, representations, or conditions of any kind, whether express or implied. The responsibilities and liabilities of AWS to its customers are controlled by AWS agreements, and this document is not part of, nor does it modify, any agreement between AWS and its customers, and 

(d) is not to be considered a recommendation or viewpoint of AWS. 

Additionally, you are solely responsible for testing, security and optimizing all code and assets on GitHub repo, and all such code and assets should be considered: 

(a) as-is and without warranties or representations of any kind, 

(b) not suitable for production environments, or on production or other critical data, and 

(c) to include shortcuts in order to support rapid prototyping such as, but not limited to, relaxed authentication and authorization and a lack of strict adherence to security best practices. 

All work produced is open source. More information can be found in the GitHub repo. 

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



