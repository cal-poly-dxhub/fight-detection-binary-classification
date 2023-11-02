import boto3
import cv2
import math
import os
import subprocess
from time import sleep

LOCAL_RUN = True


if LOCAL_RUN:
    # ----- use to connect to client locally -----
    session = boto3.Session(profile_name='PROFILE')
    ecs = session.client('ecs')
    s3_client = session.client('s3')
    s3 = session.resource('s3')

else:
    # ----- use when creating / running ecs task -----
    ecs = boto3.client('ecs')
    s3_client = boto3.client('s3')
    s3 = boto3.resource('s3')


SOURCE_MP4_VIDEO_BUCKET = 'video-mp4'
OUTPUT_IMAGE_BUCKET = 'unlabeled-images'

SOURCE_AVI_VIDEO_BUCKET = 'video-avi'
OUTPUT_MP4_VIDEO_BUCKET = 'video-mp4'



if LOCAL_RUN:
    # ----- use for local directories -----
    TEMP_DIRECTORY = "../tmp/"
    SOURCE_VIDEO_DIRECTORY = "../source_videos/"

else:
    # ----- use when creating / running ECS task -----
    TEMP_DIRECTORY = "./tmp/"
    SOURCE_VIDEO_DIRECTORY = "./source_videos/"

MAX_VIDEO_DURATION_SECONDS = 240


def main():


    mp4_files = get_files_in_mp4_bucket()

    
    download_files_to_process(mp4_files)

    for file_name in mp4_files:
        print("FILE IS " + file_name)
        upload_frames(file_name)
        clear_temp_folder()

    clear_source_video_folder()


'''''''''
Goal: Determine which files in the .avi bucket have not been processed
Return: List of file names that have not been processed
'''''''''
def get_files_in_mp4_bucket():
    print("Determining files to process...")

    mp4_bucket = s3.Bucket(OUTPUT_MP4_VIDEO_BUCKET)
    mp4_files = list(map(lambda x: x.key, mp4_bucket.objects.all()))
    
   

    if len(mp4_files) == 0:
        print(f"No files in {SOURCE_AVI_VIDEO_BUCKET} to process")

    return mp4_files


'''''''''
Goal: Download all files that must be processed
Return: None
'''''''''
def download_files_to_process(files_to_process):
    for file_name in files_to_process:
        print("Downloading File: " + file_name)
        s3_client.download_file(Bucket=OUTPUT_MP4_VIDEO_BUCKET,
                                Key=file_name,
                                Filename=SOURCE_VIDEO_DIRECTORY + file_name)


'''''''''
Goal: Convert files to MP4, upload MP4 to S3, and upload frame jpgs to S3
Return: None
'''''''''
def process_file(file_name):
    print("Processing: " + file_name)
    duration = get_file_duration(file_name)

    if duration > MAX_VIDEO_DURATION_SECONDS:
        num_clips = split_and_convert_file(file_name, duration)

    else:
        num_clips = convert_file(file_name)

    upload_frames(file_name, num_clips)



'''''''''
Goal: Determine duration of file
Return: Duration of file
'''''''''
def get_file_duration(file_name):
    print("Getting File Duration: ", SOURCE_VIDEO_DIRECTORY + file_name)
    cam = cv2.VideoCapture(SOURCE_VIDEO_DIRECTORY + file_name)
    frame_count = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cam.get(cv2.CAP_PROP_FPS)
    duration = int(frame_count / fps)

    return duration



'''''''''
Goal: Split file into pieces before converting to .MP4 and upload each converted file to S3
Return: The number of clips that were uploaded
'''''''''
def split_and_convert_file(file, duration):
    print("Splitting " + file + " and converting to MP4...")

    base_file_name = file.lower().replace(".avi", "")
    file_name_in_source_dir = file.replace(".avi", "")

    subprocess.call(
        ["ffmpeg", "-i", SOURCE_VIDEO_DIRECTORY+ file, "-c:v", "libx264", "-reset_timestamps", "1", "-max_muxing_queue_size",
         "8192", "-segment_time",
         "120", "-sc_threshold", "0", "-f", "segment", '-force_key_frames', "expr: gte(t, n_forced*120)",
         f"{TEMP_DIRECTORY}{base_file_name}---%03d.mp4"])

    num_clips = math.ceil(duration / 120)

    fight_num = get_max_fight_num(list(map(lambda x: x.key, s3.Bucket(OUTPUT_MP4_VIDEO_BUCKET).objects.all()))) + 1
    for clip_num in range(num_clips):
        upload_mp4(base_file_name, fight_num, clip_num)

    # upload_avi(file_name_in_source_dir, fight_num)
    return num_clips


'''''''''
Goal: Convert a file to .MP4 and upload it to S3
Return: Number of clips uploaded
'''''''''
def convert_file(file):
    base_file_name = file.lower().replace(".avi", "")
    file_name_in_source_dir = file.replace(".avi", "")
    mp4_file_name = file.lower().replace(".avi", ".mp4")

    print("Converting " + file + " to MP4...")
    subprocess.call(['ffmpeg', '-i', SOURCE_VIDEO_DIRECTORY + file, "-max_muxing_queue_size", '8192',
                     TEMP_DIRECTORY + mp4_file_name.replace(".mp4", "---000.mp4")])

    fight_num = get_max_fight_num(list(map(lambda x: x.key, s3.Bucket(OUTPUT_MP4_VIDEO_BUCKET).objects.all()))) + 1
    upload_mp4(base_file_name, fight_num)
    # upload_avi(file_name_in_source_dir, fight_num)

    return 1


'''''''''
Goal: Upload clip to S3
Return: None
'''''''''
def upload_mp4(base_file_name, fight_num, clip_num=0):
    clip_postfix = f"---{clip_num:03d}"
    mp4_file_name = base_file_name + clip_postfix + ".mp4"
    fight_name = "Fight_" + str(fight_num)
    upload_mp4_file_name = fight_name + clip_postfix + ".mp4"

    print("Uploading " + mp4_file_name + " as " + upload_mp4_file_name)
    s3_client.upload_file(TEMP_DIRECTORY + mp4_file_name, OUTPUT_MP4_VIDEO_BUCKET, upload_mp4_file_name)


def upload_avi(base_file_name, fight_num):
    avi_file_name = base_file_name + ".avi"

    fight_name = "Fight_" + str(fight_num)
    upload_avi_file_name = fight_name + ".avi"
    print("Uploading " + avi_file_name + " as " + upload_avi_file_name)
    s3_client.upload_file(SOURCE_VIDEO_DIRECTORY + avi_file_name, SOURCE_AVI_VIDEO_BUCKET, upload_avi_file_name)


'''''''''
Goal: Upload every 10th frame to S3 for labeling for a given clip
Return: None
'''''''''
def upload_frames(file_name):
    
    cam = cv2.VideoCapture(SOURCE_VIDEO_DIRECTORY + file_name)
    fps = cam.get(cv2.CAP_PROP_FPS)
    frame_increment = int(fps / 2)
    print("frame increment", frame_increment)
    currentframe = 0
    target_frame = 0

    fight_num = file_name.split('---')[0].split('_')[1]
    # clip_postfix = f"---{clip_num:03d}"

    
    while True:
        ret, frame = cam.read()
        if not ret:
            break
    
        
        if currentframe == target_frame:
            
            frame_name = file_name.replace(".mp4", "") + '_frame_' + str(currentframe) + '.jpg'
            cv2.imwrite(TEMP_DIRECTORY + frame_name, frame)
            target_frame += frame_increment

            print("Uploading frame: " + frame_name)
            s3_client.upload_file(TEMP_DIRECTORY + frame_name,
                                    OUTPUT_IMAGE_BUCKET,
                                    frame_name)

        currentframe += 1

    # Release all space and windows once done
    cam.release()
    cv2.destroyAllWindows()



def get_max_fight_num(mp4_files):
    max_fight_num = -1
    for file in mp4_files:
        fight_num = int(file.split("_")[1].split("---")[0])
        if fight_num > max_fight_num:
            max_fight_num = fight_num

    return max_fight_num

def clear_temp_folder():
    for file in os.listdir(TEMP_DIRECTORY):
        os.remove(os.path.join(TEMP_DIRECTORY, file))


def clear_source_video_folder():
    for file in os.listdir(SOURCE_VIDEO_DIRECTORY):
        os.remove(os.path.join(SOURCE_VIDEO_DIRECTORY, file))


'''''''''
Goal: Remove original avi file since it has now been reuploaded with a proper name
Return: None
'''''''''
def remove_original_avi_file(file_name):
    s3_client.delete_object(Bucket=SOURCE_AVI_VIDEO_BUCKET,
                            Key=file_name)

if __name__ == "__main__":
    main()

