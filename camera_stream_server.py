import zmq
import threading
from queue import Queue
import numpy as np
from PIL import Image
import io
import logging
from config import Config as cfg

class CameraStreamServer:
    ''''
    This is a implementation of a ZMQ image stream receiver for the SlamCar project.
    '''
    def __init__(self, port=cfg.get('image_stream_port')):
        self.host = '0.0.0.0'
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://{self.host}:{self.port}")
        self.queue = Queue()
        self._thread = threading.Thread(target=self._receive_loop, daemon=True)

    def start(self):
        self._thread.start()
        print(f"Image Stream: Listening at {self.host}:{self.port}")

    def receive_image(self):
        if not self.queue.empty():
            return self.queue.get()
        else:
            return None

    def close(self):
        print("Closing socket")
        self.socket.close()
        self.context.term()
        
    def _receive_loop(self):
        while True:
            message = self.socket.recv()
            try:
                # Extract the size of the message and the image bytes
                size = int.from_bytes(message[:4], byteorder='big')
                img_bytes = message[4:4+size]
                # Convert the bytes to an image
                img = Image.open(io.BytesIO(img_bytes))
                img = np.array(img)
                # Put the image in the queue for the main thread to consume
                self.queue.put(img)

                self.socket.send(b'OK')
            except:
                self.socket.send(b'ERROR')

