
import sys
import numpy as np
import cv2
import logging


class CarModel:
    def __init__(self, x=0, y=0, theta=0):
        self.pos = np.array([x, y], dtype=np.float32) # m (x, y)
        self.theta = theta # orientation (rad) (0 = east, pi/2 = north, pi = west, 3/2 pi = south)

        self.tire_angle = 0       # rad (0 = straight, positive = left, negative = right)
        self.tire_angle_max = np.pi/4 # rad 

        self.velocity = 0    # m/s   (linear velocity)
        self.angular_velocity = 0 # rad/s (angular velocity)

        self.dt = 0.1     # s (time step)

        self.length = 0.3 # m (length of car from tire to tire)
        self.width = 0.2  # m (width of car)

        self.rotation_point = np.array([0, 0], dtype=np.float32)

    def move(self):
        
        dpos = self.velocity * np.array([np.cos(self.theta), np.sin(self.theta)], dtype=np.float32)
        dtheta = self.velocity * np.tan(self.tire_angle) / self.length

        self.pos += dpos * self.dt 
        self.theta += dtheta * self.dt


    def set_velocity(self, v):
        self.velocity = v

    def set_tire_angle(self, tire_angle):
        self.tire_angle = tire_angle

        if self.tire_angle > self.tire_angle_max:
            self.tire_angle = self.tire_angle_max
        elif self.tire_angle < -self.tire_angle_max:
            self.tire_angle = -self.tire_angle_max

    def get_tire_angle(self):
        return self.tire_angle
    
    def get_velocity(self):
        return self.velocity


class Visualization2D():
    def __init__(self, car_model):
        self.car_model = car_model

        self.img = np.zeros((500, 500, 3), np.uint8)

        self.img_center = (250, 250)
        self.img_scale = 100
        self.car_size = (self.car_model.length * self.img_scale, self.car_model.width * self.img_scale)

    def draw_car(self):
        self.img *= 0

        x = self.img_center[0] + self.car_model.pos[0] * self.img_scale
        y = self.img_center[1] - self.car_model.pos[1] * self.img_scale

        theta = self.car_model.theta

        #draw rotated rectangle
        pts = np.array([[x - self.car_size[0], y - self.car_size[1]], 
                        [x + self.car_size[0], y - self.car_size[1]], 
                        [x + self.car_size[0], y + self.car_size[1]], 
                        [x - self.car_size[0], y + self.car_size[1]]], np.int32)
        pts = pts.reshape((-1, 1, 2))
        rot_mat = cv2.getRotationMatrix2D((x, y), theta * 180 / np.pi, 1)
        pts = cv2.transform(pts, rot_mat)
        cv2.fillPoly(self.img, [pts], (255, 255, 255))


        # draw car front
        cv2.line(self.img, (int(x), int(y)), (int(x + 20 * np.cos(theta)), int(y - 20 * np.sin(theta))), (0, 0, 0), 2)

        # draw rotation point
        cv2.circle(self.img, (int(x + self.car_model.rotation_point[0] * self.img_scale), int(y - self.car_model.rotation_point[1] * self.img_scale)), 5, (0, 0, 255), -1)




def simulate_input(k, car_model):
    global steering, velocity

    if k == ord('a'):
        steering -= 0.1
    elif k == ord('d'):
        steering += 0.1
    elif k == ord('w'):
        velocity += 0.1
    elif k == ord('s'):
        velocity -= 0.1
    steering *= 0.95
    velocity *= 0.95

    if steering > car_model.tire_angle_max:
        steering = car_model.tire_angle_max
    elif steering < -car_model.tire_angle_max:
        steering = -car_model.tire_angle_max

    if velocity > 1:
        velocity = 1

    #logging.info('steering: %f, velocity: %f', steering, velocity)

    car_model.set_velocity(velocity)
    car_model.set_tire_angle(steering)



if __name__ == '__main__':
    car_model = CarModel(0, 0, 0)

    vis = Visualization2D(car_model)
    
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    k = None

    steering = 0.0
    velocity = 0.0
    while k != 27:

        #simulate_input(k, car_model)
        car_model.set_velocity(0.1)
        car_model.set_tire_angle(0.3)

        car_model.move()
        vis.draw_car()


        cv2.imshow('img', vis.img)
        k = cv2.waitKey(10)
