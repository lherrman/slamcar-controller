import zmq
import threading
from queue import Queue
import numpy as np
from PIL import Image
from config import Config as cfg


class ControllStreamServer:
    ''''
    This is a implementation of a ZMQ image stream receiver for the SlamCar project.
    '''
    def __init__(self, port=cfg.get('controll_port')):
        self.host = '0.0.0.0'
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://{self.host}:{self.port}")
        self._thread = threading.Thread(target=self._communication_loop, daemon=True)

        self.controlls = { # the controlls for the car
            'throttle': 10,
            'steering': 0
        }

        self.state = { # the feedback from the car
            'throttle': 0,
            'steering': 0,
        }

        self.config_queue = Queue() # the config queue
        
        self.controll_lock = threading.Lock()
        self.state_lock = threading.Lock()

    def start(self):
        self._thread.start()
        print(f"Controll Stream: Listening as {self.host}:{self.port}")


    def close(self):
        print("Closing socket")
        self.socket.close()
        self.context.term()
        
    def _communication_loop(self):
        while True:
            message = self.socket.recv_json()

            with self.state_lock:
                self.state = message


            with self.controll_lock:
                if not self.config_queue.empty():
                    config = self.config_queue.get()
                    package = {
                        "controlls": self.controlls,
                        "config": config
                    }
                    self.socket.send_json(package)
                else:
                    package = {
                        "controlls": self.controlls,
                        "config": False
                    }
                    self.socket.send_json(package)


    def send_config(self, config):
        self.config_queue.put(config)


if __name__ == '__main__':
    import time
    controll_server = ControllStreamServer()
    controll_server.start()
    n = 0
    while True:
        with controll_server.state_lock:
            print(controll_server.state)
        with controll_server.controll_lock:
            controll_server.controlls['throttle'] = n
            controll_server.controlls['steering'] = 0.5
            n += 1
        time.sleep(0.05)