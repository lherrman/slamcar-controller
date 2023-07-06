
import cv2
import numpy as np
import pyfakewebcam
import time
import subprocess

class StellaConnector:
    '''
    This class sends frames to a virtual v4l2 webcam device that can be mounted in the docker container running stella_vslam.
    '''
    def __init__(self, image_size):
        height, width, _ = image_size
        virtual_device_name = self._get_virtual_device_name()
        self.virtual_cam = pyfakewebcam.FakeWebcam(virtual_device_name, width, height)

    def _get_virtual_device_name(self) -> str:
        try:
            output = subprocess.check_output('ls -1 /sys/devices/virtual/video4linux', shell=True)
        except subprocess.CalledProcessError:
            raise Exception('Virtual device does not exist. Please create it using the following command: sudo modprobe v4l2loopback video_nr=1')
        return f'/dev/{output.decode("utf-8").strip()}'

    def send_image(self, image: np.ndarray):
        frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.virtual_cam.schedule_frame(frame)

        

if __name__ == "__main__":
    capture = cv2.VideoCapture(0)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    stella_connector = StellaConnector((480, 640, 3))

    ret, frame = capture.read()
    while ret:
        stella_connector.push_image(frame)
        ret, frame = capture.read()
        time.sleep(0.1)
        cv2.imshow('Video Stream', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    capture.release()
    cv2.destroyAllWindows()

