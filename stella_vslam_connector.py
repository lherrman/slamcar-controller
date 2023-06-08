
import cv2
import numpy as np
import pyfakewebcam
import time


def main():
    video_file_path = "./stella_data/video.mp4"
    cap = cv2.VideoCapture(video_file_path)
    fake = pyfakewebcam.FakeWebcam('/dev/video4', 640, 480) # replace X with the number of the virtual video device

    frame_rate = 30
    # loop through the frames in the video file
    while True:
        # read a frame from the video file
        ret, frame = cap.read()

        # check if we've reached the end of the video file
        if not ret:
            break

        # resize the frame to 640x480
        frame = cv2.resize(frame, (640, 480))

        # convert the frame to RGB format
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # write the frame to the fake webcam
        fake.schedule_frame(frame)

        # wait until the next frame
        time.sleep(1.0 / frame_rate)
        
    # release the video file and the fake webcam
    cap.release()
    fake.stop()

if __name__ == '__main__':
    main()