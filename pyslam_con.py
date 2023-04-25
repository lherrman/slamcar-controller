


import numpy as np
import cv2

class PySlamCon():
    def __init__(self, image_dir):
        self.image_dir = image_dir
        self.i = 0 # the image counter

    def put_image(self, image):
        outpath = self.image_dir + f'\\{str(self.i).zfill(5)}.jpg'
        self.i += 1
        cv2.imwrite(outpath, image)