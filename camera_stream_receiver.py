import cv2
import ffmpeg
import numpy as np
import time
import threading

class CameraStreamReceiver:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port

        self.thread = threading.Thread(target=self.receive_stream)

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread = None
        

    def receive_stream(self):
        while True:
            print('Connecting to %s:%d' % (self.server_ip, self.server_port))
            try:
                process = (
                    ffmpeg
                    .input('tcp://%s:%d' % (self.server_ip, self.server_port), format='flv')
                    .output('pipe:', format='rawvideo', pix_fmt='bgr24')
                    .run_async(pipe_stdout=True)
                )
                while True:
                    in_bytes = process.stdout.read(480 * 640* 3)  # read bytes from the stdout pipe
                    if not in_bytes:
                        break
                    in_frame = (
                        np
                        .frombuffer(in_bytes, np.uint8)
                        .reshape([480, 640, 3])
                    )
                    cv2.imshow('Video Stream', in_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            except Exception as e:
                print('Connection failed:', e)
                time.sleep(5)
            finally:
                cv2.destroyAllWindows()
                if 'process' in locals():
                    process.stdout.close()
                    process.wait()

if __name__ == "__main__":
    receiver = CameraStreamReceiver('127.0.0.1', 8000)
    threading.Thread(target=receiver.receive_stream).start()
