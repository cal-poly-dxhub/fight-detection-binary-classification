import cv2
from datetime import datetime
import time
import os
import glob

# the max number of frames we want to capture regardless of camera FPS
FRAME_PER_SECOND_MAX = 2
MIN_CONFIDENCE = 1
SOURCE_VIDEO_DIRECTORY = '/demo/vid'
OUTPUT_IMAGE_DIRECTORY = '/demo/images'
    

def slice_into_images(file_name):
    
    print("Starting",file_name)
    cam = cv2.VideoCapture(file_name)
    
    # with so many FPS we want to only upload frames 2 FPS max
    # frame we are currently processing
    current_frame = 0
    # frame we want to upload
    target_frame = 0

    fps = cam.get(cv2.CAP_PROP_FPS)
    print("FPS=", fps)
    #
    capture_every_x_frame = int(fps / FRAME_PER_SECOND_MAX)

    num_frames = 0
    extracted_frame = 0
    fight_count = 0
    
    while True:
       
        ret, frame = cam.read()
        if not ret:
            break
        
        if current_frame == target_frame:
            # grab video file name and build string for output image
            # Note unix specific path
            start_name = file_name.rindex('/')
            frame_name = file_name[start_name:-3] + '-frame-' +str(extracted_frame)  + '.jpg'
            
            #start = datetime.now()
            cv2.imwrite(OUTPUT_IMAGE_DIRECTORY+'/'+frame_name, frame)
          
            target_frame += capture_every_x_frame
            extracted_frame +=1
            #start = datetime.now()
            #s3_client.upload_file(fight_image, "images-upload", frame_name)
            #print("S3 upload took ", datetime.now()-start)
        num_frames += 1
        current_frame += 1
        # if current_frame == 40:
        #     break        
    #write_csv_record(image_files)
    # Release all space and windows once done
    cam.release()
    cv2.destroyAllWindows()




#with open('files.txt') as csv_file:
#    csv_reader = csv.reader(csv_file, delimiter=',')
#    counter = 0
#    for f in csv_reader:
#        image_file = TEMP_DIRECTORY + f[0]


def main():
    # process all files in source dir

    files_to_process = glob.glob(SOURCE_VIDEO_DIRECTORY+"/*.mp4")
    print(files_to_process)
    for vidfile in files_to_process:
        slice_into_images(vidfile)

if __name__ == "__main__":
    main()
