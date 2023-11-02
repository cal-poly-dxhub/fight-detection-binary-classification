# import cv2

# print("Starting")
# #print(cv2.getBuildInformation())
# #cap = cv2.VideoCapture("rtsp://192.168.1.14:554/live1.sdp")
# vid_capture = cv2.VideoCapture("rtsp://192.168.1.14:554/live1.sdp", cv2.CAP_QT)
# while(vid_capture.isOpened()):
#     print("Open")
#     ret, frame = vid_capture.read()
#     cv2.imshow('frame', frame)
#     if cv2.waitKey(20) & 0xFF == ord('q'):
#         print("Show")
#         break
#     vid_capture.release()
# cv2.destroyAllWindows()
import cv2
import numpy as np
import os

TEMP_DIRECTORY = './tmp/'
print(cv2.getBuildInformation())
#os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
frame_count = 0
#vcap = cv2.VideoCapture("rtsp://admin:admin@192.168.1.61:554/live1.sdp")
vcap = cv2.VideoCapture("rtsp://admin:admin@192.168.1.100/defaultPrimary-0?streamType=u")
vcap = cv2.VideoCapture(0)
while(frame_count < 100):
    
    
    ret, frame = vcap.read()
   
    if ret == False:
        print("Frame is empty")
        ret, frame = vcap.read()
        print(ret)
    else:
        frame_name = "ip-camera-" + str(frame_count) + '.jpg'
        #cv2.imshow('VIDEO', frame)
        #cv2.waitKey(1)
        cv2.imwrite(TEMP_DIRECTORY + frame_name, frame)
        frame_count += 1

    vcap.release()