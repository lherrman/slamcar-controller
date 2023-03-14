from base_model import BasemodelController
import numpy as np
from pprint import pprint
import threading
import time

class SlamcarController():
    def __init__(self):
        self.baseline_controller = BasemodelController()

    def run(self):
        self.baseline_controller.run()

if __name__ == '__main__':
    controller = SlamcarController()
    controller.run()
