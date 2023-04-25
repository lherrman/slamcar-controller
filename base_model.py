import numpy as np
import math
import pygame as pg
from pygame.math import Vector2

from config import Config as cfg

class CarModel:
    def __init__(self, x, y):
        self.length = 0             # length of the car in meters
        self.width = 0              # width of the car in meters
        self.max_velocity = 0       # meters per second
        self.acceleration_speed = 0 # meters per second
        self.steering_speed =   0   # degrees per second
        self.max_steering = 0       # degrees
        self.load_parameters()

        self.position = Vector2(x, y)                # position in meters
        self.heading = Vector2(0, -1).normalize()    # heading towards the front of the car
        self.velocity = Vector2(0.0, 0.0)            # velocity in meters per second
        self.velocity_magnitude = 0.0                # velocity magnitude in meters per second
        self.steering = 0.0                          # tire angle in degrees
        self.steering_radius = 0.0                   # radius of the circle the car is moving on
        self.steering_rotation_point = Vector2(0, 0) # point around which the car is rotating
        self.rotation_position = -1                  # 1.0 = front, -1.0 = back

        self.magic_number = 0.014 # temporary fix for bug with velocity calculation

        self.camera_position = Vector2(0, 0) # position of the camera in the world
        self.camera_position_smooth = Vector2(0, 0) # smoothed position of the camera in the world

        self.ppu = 64           # pixels per unit
        self.draw_track_projection = False # draw the track the car is moving on

        self._trace = [] # list of points that the car has passed
        self.draw_track = True # draw the track the car has passed

        self.trace_tires = [[],[]] # list of points that the tires have passed

    def update(self, dt):
        self._update_position(dt)
        self._update_trace()
        self._update_inputs(dt)
        self._calculate_steering_rotation_point()

    def load_parameters(self):
        self.length = cfg.get("car_length")
        self.width = cfg.get("car_width")
        self.max_steering = cfg.get("max_steering")
        self.max_velocity = cfg.get("max_velocity")
        self.acceleration_speed = cfg.get("acceleration")
        self.steering_speed = cfg.get("steering_speed")

    def _update_position(self, dt):
        # If steering is 0, move in a straight line
        # Otherwise, move in a circle around steering_rotation_point
        if np.abs(self.steering) < 0.01:
            self.velocity = self.heading.normalize() * self.velocity_magnitude
            self.position += self.velocity * dt * self.magic_number 
        else:
            angular_velocity = self.velocity_magnitude / self.steering_radius
            self.heading = self.heading.rotate(angular_velocity * dt)
            self.position = self._rotate_vector_about_point(self.position, 
                                                            self.steering_rotation_point, 
                                                            angular_velocity * dt)
    def _update_inputs(self, dt):
        pressed = pg.key.get_pressed()

        # Steering
        self._update_steering(pressed[pg.K_a], pressed[pg.K_d], dt)
        self.steering_radius = self._calculate_steering_radius()

        # Velocity
        self._update_velocity(pressed[pg.K_w], pressed[pg.K_s], dt)

        # Debug Keys
        if pressed[pg.K_m]:
            self.magic_number += 0.001
        if pressed[pg.K_n]:
            self.magic_number -= 0.001  

    def _calculate_steering_radius(self):
        if self.steering == 0:
            return 0
        else:
            return self.length / math.tan(math.radians(self.steering))
        
    def _update_steering(self, left, right, dt):
        if left:
            self.steering = max(-self.max_steering, self.steering - self.steering_speed * dt)

        if right:
            self.steering = min(self.max_steering, self.steering + self.steering_speed * dt)

        # If neither is pressed, reduce steering to 0
        # back_steer_factor determines how fast the steering will go back to 0
        back_steer_factor = 2
        if not left and not right:
            if self.steering > 0:
                self.steering = max(0, self.steering - self.steering_speed * dt * back_steer_factor)
            else:
                self.steering = min(0, self.steering + self.steering_speed * dt * back_steer_factor)
        
    def _update_velocity(self, up, down, dt):
        if up:
            self.velocity_magnitude = min(self.max_velocity, self.velocity_magnitude + self.acceleration_speed * dt)
        if down:
            self.velocity_magnitude = max(-self.max_velocity, self.velocity_magnitude - self.acceleration_speed * dt)

        # If neither is pressed, reduce velocity to 0
        if not up and not down:
            if self.velocity_magnitude > 0:
                self.velocity_magnitude = max(0, self.velocity_magnitude - self.acceleration_speed * dt)
            else:
                self.velocity_magnitude = min(0, self.velocity_magnitude + self.acceleration_speed * dt)
        
    def _update_trace(self):
        if not hasattr(self, 'temp_trace_counter'):
            self.temp_trace_counter = 1
        self.temp_trace_counter += 1

        self._trace.append(self.position)

        # Only update the trace from tires when moving fast enough
        # and every x frames
        frame_skip = 5
        if abs(self.velocity_magnitude) < 0.5 or \
            self.temp_trace_counter % frame_skip != 0:
            return
        
        angle = -self.heading.angle_to(Vector2(1, 0))
        tires = [
            Vector2(-self.length / 2, self.width / 2),
            Vector2(-self.length / 2, -self.width / 2)
        ]
        for i in range(len(tires)):
            tires[i] = tires[i].rotate(angle)
            tires[i] += self.position
            self.trace_tires[i].append(tires[i])
            
            if len(self.trace_tires[i]) > 500:
                for j in range(frame_skip):
                    self.trace_tires[i].pop(0)
    
    def _calculate_steering_rotation_point(self):
        angle = -self.heading.angle_to(Vector2(1, 0))
        self.steering_rotation_point = Vector2(0, self.steering_radius)
        self.steering_rotation_point = self.steering_rotation_point.rotate(angle)
        self.steering_rotation_point += self.rotation_position * (self.heading.normalize()  * self.length / 2 )
        #self.steering_rotation_point *= self.ppu
        self.steering_rotation_point += self.position

    def draw(self, screen, ppu):
        self.ppu = ppu

        self._update_camera_position(screen)

        self._draw_grid(screen)
        self._draw_trace(screen)
        if self.draw_track_projection: self._draw_steering_radius(screen, True)
        self._draw_tires(screen)
        self._draw_car(screen)


    def _update_camera_position(self, screen):
        self.camera_position = self.position - (Vector2(*screen.get_rect().center) / self.ppu)
        self.camera_position_smooth = self.camera_position_smooth * 0.97 + self.camera_position * 0.03

    def _draw_grid(self, screen):
        canvas_width = screen.get_width()
        canvas_height = screen.get_height()
    
        # TODO: with this method about 1/2 of the grid is drawn off screen
        start_x = int(self.camera_position_smooth.x * self.ppu) - canvas_width
        start_y = int(self.camera_position_smooth.y * self.ppu) - canvas_height
        stop_x = int(self.camera_position_smooth.x * self.ppu) + canvas_width
        stop_y = int(self.camera_position_smooth.y * self.ppu) + canvas_height
        start_x = start_x - start_x % self.ppu
        start_y = start_y - start_y % self.ppu

        for x in range(start_x, stop_x, self.ppu):
            pg.draw.line(screen, (50, 50, 50), (x - self.camera_position_smooth.x * self.ppu, 0), (x - self.camera_position_smooth.x * self.ppu, canvas_height))
        for y in range(start_y, stop_y, self.ppu):
            pg.draw.line(screen, (50, 50, 50), (0, y - self.camera_position_smooth.y * self.ppu), (canvas_width, y - self.camera_position_smooth.y * self.ppu))


    def _draw_steering_radius(self, screen, draw_wide_track=False):
        # Draw steering radius
        color_track = (25, 25, 25)
        color_line = (20, 40, 40)
        width = int(self.width * self.ppu)
        
        if self.steering_radius > 0:
            if draw_wide_track:
                pg.draw.circle(screen, color_track,
                               (self.steering_rotation_point  - self.camera_position_smooth) * self.ppu, 
                               self.steering_radius * self.ppu + width //2, width)
            pg.draw.circle(screen, color_line, 
                           (self.steering_rotation_point - self.camera_position_smooth)  * self.ppu,
                           self.steering_radius * self.ppu, 1)
        elif self.steering_radius < 0: 
            if draw_wide_track:
                pg.draw.circle(screen, color_track, 
                               (self.steering_rotation_point  - self.camera_position_smooth)  * self.ppu, 
                               -self.steering_radius * self.ppu + width // 2, width)
            pg.draw.circle(screen, color_line, 
                           (self.steering_rotation_point  - self.camera_position_smooth) * self.ppu, 
                           -self.steering_radius * self.ppu, 1)
        else:
            if draw_wide_track:
                pg.draw.line(screen, color_track,
                             (self.position  - self.camera_position_smooth) * self.ppu - self.heading * self.ppu * 100,
                             (self.position  - self.camera_position_smooth) * self.ppu + self.heading * self.ppu * 100,
                             width)
            pg.draw.line(screen, color_line,
                         (self.position  - self.camera_position_smooth)  * self.ppu - self.heading * self.ppu * 100,
                         (self.position- self.camera_position_smooth) * self.ppu + self.heading * self.ppu * 100, 1)

    def _draw_car(self, screen):
        # draw rectangle representing car
        angle = -self.heading.angle_to(Vector2(1, 0))

        factor_overlap = 1.5 # determines how much the car goes over the tires from the front and back
        car_corner_points = [
            Vector2(-self.length / factor_overlap, self.width / 2),
            Vector2(self.length / factor_overlap, self.width / 2),
            Vector2(self.length / factor_overlap, -self.width / 2),
            Vector2(-self.length / factor_overlap, -self.width / 2)
        ]

        car_corner_points = [p.rotate(angle) for p in car_corner_points]
        car_corner_points = [p + self.position for p in car_corner_points]
        car_corner_points = [p - self.camera_position_smooth for p in car_corner_points]
        car_corner_points = [p * self.ppu for p in car_corner_points]

        pg.draw.polygon(screen, (255, 255, 255), car_corner_points, 0)

        # indicate front of car
        #pg.draw.line(screen, (255, 255, 0), self.position *  self.ppu, (self.position + self.heading) * self.ppu * 0.1, 1)

    def _draw_tires(self, screen):
        # Draw tires
        angle = -self.heading.angle_to(Vector2(1, 0))
        tire_width = self.width / 4
        tire_length = self.length / 4

        # Draw front tires
        tire_corner_points = [
            Vector2(-tire_length / 2, tire_width / 2),
            Vector2(tire_length / 2, tire_width / 2),
            Vector2(tire_length / 2, -tire_width / 2),
            Vector2(-tire_length / 2, -tire_width / 2)
        ]

        tire_corner_points = [p.rotate(angle + self.steering) for p in tire_corner_points]
        tire_corner_points = [p * self.ppu for p in tire_corner_points]

        tires = [
            Vector2(self.length / 2, self.width / 2),
            Vector2(self.length / 2, -self.width / 2),
        ]

        tires = [p.rotate(angle) for p in tires]
        tires = [p + self.position for p in tires]
        tires = [p - self.camera_position_smooth for p in tires]
        tires = [p * self.ppu for p in tires]


        for tire in tires:
            points = [p + tire for p in tire_corner_points]
            pg.draw.polygon(screen, (255, 255, 255), points, 2)

        # Draw rear tires
        tire_corner_points = [
            Vector2(-tire_length / 2, tire_width / 2),
            Vector2(tire_length / 2, tire_width / 2),
            Vector2(tire_length / 2, -tire_width / 2),
            Vector2(-tire_length / 2, -tire_width / 2)
        ]
        tire_corner_points = [p.rotate(angle) for p in tire_corner_points]
        tire_corner_points = [p * self.ppu for p in tire_corner_points]

        tires = [
            Vector2(-self.length / 2, self.width / 2),
            Vector2(-self.length / 2, -self.width / 2)
        ]
        tires = [p.rotate(angle) for p in tires]
        tires = [p + self.position for p in tires]
        tires = [p - self.camera_position_smooth for p in tires]
        tires = [p * self.ppu for p in tires]

        for tire in tires:
            points = [p + tire for p in tire_corner_points]
            pg.draw.polygon(screen, (255, 255, 255), points, 2)

    def _draw_trace(self, screen):
        for points in self.trace_tires:
            if len(points) < 2:
                continue
            points = [p - self.camera_position_smooth for p in points]
            points = [p * self.ppu for p in points]
            pg.draw.lines(screen, (50,50,50), False, points, 5)

    def _rotate_vector_about_point(self, vector, point, angle):
        """Rotate a vector about a point by a given angle in degrees."""
        vector = vector - point
        vector = vector.rotate(angle)
        vector = vector + point
        return vector

