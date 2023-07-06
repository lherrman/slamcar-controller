import cv2
import ffmpeg
import numpy as np
import time
import threading

class Sender:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port

        self.thread = threading.Thread(target=self.send_stream)

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.join()


    def send_stream(self):
        # Open the webcam device. 0 is usually the built-in webcam.
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        
        # Start the ffmpeg process
        process = (
            ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='bgr24', s='{}x{}'.format(*frame.shape[1::-1]))
            .output('tcp://%s:%d?listen=1' % (self.server_ip, self.server_port), format='flv')
            .run_async(pipe_stdin=True, pipe_stderr=True)
        )

        try:
            while True:
                # Read a frame from the webcam.
                ret, frame = cap.read()

                if not ret:
                    break
                
                # Write the raw video frame to the ffmpeg process's standard input.
                process.stdin.write(
                    frame
                    .astype(np.uint8)
                    .tobytes()
                )

        except Exception as e:
            print('Failed to send frame:', e)

        finally:
            # Clean up the ffmpeg process.
            process.stdin.close()
            process.wait()

            # Clean up the OpenCV window.
            cv2.destroyAllWindows()
            cap.release()
            

if __name__ == "__main__":
    sender = Sender('127.0.0.1', 8000)
    sender.start()
    #threading.Thread(target=sender.send_stream).start()
