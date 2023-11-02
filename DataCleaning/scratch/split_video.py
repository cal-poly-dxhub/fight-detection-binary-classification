import boto3
import os
import subprocess
import numpy as np
import cv2
from pydub import AudioSegment
import moviepy.editor as mp

# ------ MACROS ------
CV2_FRAME_RATE = cv2.CAP_PROP_FPS
SIM_FRAME_RATE = 30

BUCKET_NAME = 'mock-output-images'
SOURCE_VIDEO_PREFIX = 'source_video/'
IMAGES_PREFIX = 'images/'
VIDEO_WITHOUT_AUDIO_PREFIX = 'video_without_audio/'
AUDIO_PREFIX = 'audio/'
VIDEO_WITH_AUDIO_PREFIX = 'video_with_audio/'

TEMP_DIRECTORY = './tmp/'

# session = boto3.Session(profile_name='mike-personal')
# s3_client = session.client('s3')

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

def main():
    input_file_name = "walking.mov"
    # print("converting file")
    # mov_file_name = convert_to_mp4(input_file_name)

    s3_client.download_file(Bucket=BUCKET_NAME,
                            Key=SOURCE_VIDEO_PREFIX + input_file_name,
                            Filename=TEMP_DIRECTORY + input_file_name)

    cam = cv2.VideoCapture(TEMP_DIRECTORY + input_file_name)
    print("STEP: Getting video info")
    video_info = get_duration(cam)

    print("STEP: Splitting file into frames")
    split_video(input_file_name, video_info)
    print("STEP: Removing dead frames")
    remove_dead_frames(video_info, input_file_name, cam)

    clear_temp_folder()


def convert_to_mp4(input_file_name):
    """
    Converts all videos in ../data/video to .mp4

    Flags: -rm removes original video
    """
    try:
        _format = ''
        if ".flv" in input_file_name.lower():
            _format = ".flv"
        if ".mp4" in input_file_name.lower():
            _format = ".mp4"
        if ".avi" in input_file_name.lower():
            _format = ".avi"
        if ".mov" in input_file_name.lower():
            _format = ".mov"

        s3_client.download_file(Bucket=BUCKET_NAME,
                                Key=SOURCE_VIDEO_PREFIX + input_file_name,
                                Filename=TEMP_DIRECTORY + input_file_name)

        mov_file_name = input_file_name.lower().replace(_format, ".mp4")
        mp4_file_path = TEMP_DIRECTORY + input_file_name.lower().replace(_format, ".mp4")
        subprocess.call(['ffmpeg', '-i', TEMP_DIRECTORY + input_file_name, mp4_file_path])

        #If we want to upload the mp4s to S3 include this line, but I don't think it's necessary
        #s3_client.upload_file(output_file_path, BUCKET_NAME, SOURCE_VIDEO_PREFIX + output_file_name)

        return mov_file_name

    except Exception as e:
        print("An exception occurred: {}".format(e))


def split_video(mov_file_name, video_info):
    """
    Split video in ../data/video into frames saved to ../data/imgs
    """

    # Read the video from specified path
    cam = cv2.VideoCapture(TEMP_DIRECTORY + mov_file_name)

    currentframe = 0

    target_frame = 0
    frame_increment = int(video_info.get("fps") / 2)

    while True:
        ret, frame = cam.read()

        if not ret:
            break

        if currentframe == target_frame:
            frame_name = mov_file_name.replace(".mov", "") + '_frame_' + str(currentframe) + '.jpg'
            cv2.imwrite(TEMP_DIRECTORY + frame_name, frame)
            target_frame += frame_increment

        # If we want to upload the frames:
        # s3_client.upload_file(TEMP_DIRECTORY + frame_name,
        #                       BUCKET_NAME,
        #                       IMAGES_PREFIX + mov_file_name.replace(".mp4", "") + 'frame-' + str(currentframe) + '.jpg')

        # increasing counter so that it will
        # show how many frames are created
        currentframe += 1

    # Release all space and windows once done
    cam.release()
    cv2.destroyAllWindows()


def get_duration(cam):
    """
    Retrieve basic information about video
    """

    fps = cam.get(cv2.CAP_PROP_FPS)      # OpenCV2 version 2 used "CV_CAP_PROP_FPS"
    frame_count = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count/fps

    return {
        'fps': fps,
        'frame_count': frame_count,
        'duration_s': duration,
        'seconds': duration % 60,
        'minutes': int(duration / 60)
    }


def clear_temp_folder():
    for file in os.listdir(TEMP_DIRECTORY):
        os.remove(os.path.join(TEMP_DIRECTORY, file))


def remove_dead_frames(video_info, mov_file_name, cam):
    try:
        base_file_name = mov_file_name.replace(".mov", "")
        image_directory_content = os.listdir(TEMP_DIRECTORY)
        frames = list(filter(lambda image: image.endswith(".jpg"), image_directory_content))
        num_total_frames = int(video_info.get("duration_s") * video_info.get("fps"))
        frames.sort()
        frame_increment = int(video_info.get("fps")/2)
        percent_diff_threshold = 3

        active_clips = []

        active_audio = []

        recording_audio = False

        print("STEP: Analyzing dead frames")

        for frame_number in range(0, num_total_frames, frame_increment):
            if frame_number + frame_increment < num_total_frames:
                img1 = cv2.imread(TEMP_DIRECTORY + base_file_name + "_frame_" + str(frame_number) + ".jpg")
                img2 = cv2.imread(TEMP_DIRECTORY + base_file_name + "_frame_" + str(frame_number + frame_increment) + ".jpg")
                absolute_difference = cv2.absdiff(img1, img2).astype(np.uint8)
                threshold_difference = cv2.threshold(absolute_difference, 10, 255, cv2.THRESH_BINARY)[1]
                percent_diff = (np.count_nonzero(threshold_difference) * 100) / absolute_difference.size
                if percent_diff > percent_diff_threshold:
                    if not recording_audio:
                        timestamp = (frame_number / video_info.get("fps"))
                        recording_audio = True
                        active_audio.append(timestamp * 1000)

                    active_clips.append(frame_number)
                else:
                    if recording_audio:
                        timestamp = (frame_number / video_info.get("fps"))
                        recording_audio = False
                        active_audio.append(timestamp * 1000)

        final_frames = []
        if len(active_clips) > 0:

            for base_frame in active_clips:
                cam.set(1, base_frame)
                for increment in range(frame_increment + 1):
                    ret, frame = cam.read()
                    final_frames.append(frame)

            height, width, layers = final_frames[0].shape
            size = (width, height)
            video_writer = cv2.VideoWriter(TEMP_DIRECTORY + base_file_name + "_no_audio.mp4",
                                           cv2.VideoWriter_fourcc(*'mp4v'),
                                           video_info.get("fps"),
                                           size)

            for frame in final_frames:
                video_writer.write(frame)

            # EXTRACTING AUDIO
            movie_py_video = mp.VideoFileClip(TEMP_DIRECTORY + mov_file_name)
            movie_py_video.audio.write_audiofile(TEMP_DIRECTORY + base_file_name + "_full_audio.mp3")
            all_audio = AudioSegment.from_mp3(TEMP_DIRECTORY + base_file_name + "_full_audio.mp3")

            if len(active_audio) % 2 != 0:
                active_audio.append((len(frames) / video_info.get("fps") * 1000))

            final_audio = AudioSegment.empty()

            for time in range(0, len(active_audio), 2):
                final_audio += all_audio[active_audio[time]: active_audio[time + 1]]

            final_audio.export(TEMP_DIRECTORY + base_file_name + "_trimmed_audio.mp3", format="mp3")

            video_writer.release()

            subprocess.call(["ffmpeg",
                             "-i",  TEMP_DIRECTORY + base_file_name + "_no_audio.mp4",
                             "-i", TEMP_DIRECTORY + base_file_name + "_trimmed_audio.mp3",
                             "-c:v", "copy",
                             "-map", "0:v",
                             "-map", "1:a",
                             "-shortest", TEMP_DIRECTORY + base_file_name + "_final.mp4"])

            s3_client.upload_file(TEMP_DIRECTORY + base_file_name + "_no_audio.mp4",
                                  BUCKET_NAME,
                                  VIDEO_WITHOUT_AUDIO_PREFIX + base_file_name + "_no_audio.mp4")

            s3_client.upload_file(TEMP_DIRECTORY + base_file_name + "_trimmed_audio.mp3",
                                  BUCKET_NAME,
                                  AUDIO_PREFIX + base_file_name + "_trimmed_audio.mp3")

            s3_client.upload_file(TEMP_DIRECTORY + base_file_name + "_final.mp4",
                                  BUCKET_NAME,
                                  VIDEO_WITH_AUDIO_PREFIX + base_file_name + "_final.mp4")

    except Exception as e:
        print(e)


main()
