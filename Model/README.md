# Model
All code related to the rekognition model, manifests, and model usage.


## **Files / Folders**



### **FinalImageClassificationManifests:**
* testing_ratio_adjusted.manifest: manifest used in testing of final image classification model
* training_ration_adjusted.manifest: manifest used in training of final image classification model 
* contain 80/20 no fight to fight ratio

### **SplitManifest**
* manifest_definition.py: manifest files as python object 
* manifest_split.py: function to automatically trim  manifest file 
in manifest_definition.py until 80/20 no fight to fight ratio is achieved

### **inference.py**
* run inference code locally
* given a video in ../data folder, split video
into frames and run model on 2 frames per second
* if fight is detected (3/7 frames window) upload video to fight detected bucket, create presigned url, and publish sns text with fight alert and screenshot

### **mock_live_streaming.py**
* code to simulate ElementalMedia Live splitting a video into 
frames and streaming them into upload bucket in order to stress test inference stack

### **window.py / model.py**
* two files used during the first proof of concept demo showing how to read in frames, analyze them using model, and publish sns if fight is found. 
* use window.py to run on video, detect fight, and send response
    * expects ../data/video, ../tmp, and ../data/imgs directories 
* use model.py to start/stop model and display image with overlay showing fight/no fight confidence for each frame