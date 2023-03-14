import zmq
import threading
from queue import Queue
import numpy as np
from PIL import Image
import io
import cv2
import time

class ImageStreamReceiver:
    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 5001
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://{self.host}:{self.port}")
        self.queue = Queue()
        self._thread = threading.Thread(target=self._receive_loop, daemon=True)

    def start(self):
        self._thread.start()
        print(f"[*] Listening as {self.host}:{self.port}")

    def receive_image(self):
        if not self.queue.empty():
            return self.queue.get()
        else:
            return None

    def close(self):
        print("Closing socket")
        # close the socket
        self.socket.close()
        # terminate the context
        self.context.term()
        
    def _receive_loop(self):
        while True:
            message = self.socket.recv()

            try:
                # Extract the size of the message
                size = int.from_bytes(message[:4], byteorder='big')

                # Extract the image bytes from the message
                img_bytes = message[4:4+size]

                # Convert the bytes to an image
                img = Image.open(io.BytesIO(img_bytes))
                img = np.array(img)

                # Put the image in the queue for the main thread to consume
                self.queue.put(img)

                # Send a response to the client
                self.socket.send(b'OK')
            except:
                # If there was an error, send an error response to the client
                self.socket.send(b'ERROR')

