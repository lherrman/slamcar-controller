import sys
import numpy as np
import cv2
import logging
import os
import math
from pyfiglet import Figlet
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg
from pygame.math import Vector2

class CarModel:
    def __init__(self, x, y, angle=0.0, length=0.4, width=0.2, max_steering=30, max_acceleration=30.0):
        self.position = Vector2(x, y)
        self.heading = Vector2(0, -1).normalize()
        self.velocity = Vector2(0.0, 0.0)
        self.velocity_magnitude = 0.0
        self.max_velocity = 20.0
        self.acceleration_speed = 2 # meters per second

        self.length = length
        self.width = width

        self.max_steering = max_steering
        self.steering_speed = 10.0 # degrees per second
        self.steering = 0.0 # degrees
        self.steering_radius = 0.0 # meters
        self.steering_rotation_point = Vector2(0, 0)

        self.rotation_position = -0.5 # 1.0 = front, -1.0 = back

        self.ppu = 64 # pixels per unit (meters)

    def update(self, dt):
        self._update_position(dt)
        self._update_inputs(dt)
        self._calculate_steering_rotation_point()

    def _update_position(self, dt):
        # If steering is 0, move in a straight line
        # Otherwise, move in a circle around steering_rotation_point
        if np.abs(self.steering) < 0.01:
            self.velocity = self.heading.normalize() * self.velocity_magnitude
            self.position += self.velocity * dt  * 0.5 # TODO: remove this magic number (recalculate all the units)
        else:
            angular_velocity = self.velocity_magnitude / self.steering_radius / (math.pi) 
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
            ...
        if pressed[pg.K_n]:
            ...


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

        # If neither W or S is pressed, reduce velocity to 0
        if not up and not down:
            if self.velocity_magnitude > 0:
                self.velocity_magnitude = max(0, self.velocity_magnitude - self.acceleration_speed * dt)
            else:
                self.velocity_magnitude = min(0, self.velocity_magnitude + self.acceleration_speed * dt)
        
    def _calculate_steering_rotation_point(self):
        angle = -self.heading.angle_to(Vector2(1, 0))
        self.steering_rotation_point = Vector2(0, self.steering_radius)
        self.steering_rotation_point = self.steering_rotation_point.rotate(angle)
        self.steering_rotation_point += self.rotation_position * (self.heading.normalize()  * self.length / 2 )
        self.steering_rotation_point *= self.ppu
        self.steering_rotation_point += self.position
        

    def draw(self, screen, ppu):
        self.ppu = ppu

        self._draw_steering_radius(screen, True)
        self._draw_tires(screen)
        self._draw_car(screen)

    def _draw_steering_radius(self, screen, draw_wide_track=False):
        # Draw steering radius
        color_track = (0, 10, 10)
        color_line = (0, 60, 60)
        width = int(self.width * self.ppu)
        
        if self.steering_radius > 0:
            if draw_wide_track:
                pg.draw.circle(screen, color_track, self.steering_rotation_point, self.steering_radius * self.ppu + width //2, width)
            pg.draw.circle(screen, color_line, self.steering_rotation_point, self.steering_radius * self.ppu, 1)
        elif self.steering_radius < 0: 
            if draw_wide_track:
                pg.draw.circle(screen, color_track, self.steering_rotation_point, -self.steering_radius * self.ppu + width // 2, width)
            pg.draw.circle(screen, color_line, self.steering_rotation_point, -self.steering_radius * self.ppu, 1)
        else:
            if draw_wide_track:
                pg.draw.line(screen, color_track, self.position - self.heading * self.ppu * 100, self.position + self.heading * self.ppu * 100, width)
            pg.draw.line(screen, color_line, self.position - self.heading * self.ppu * 100, self.position + self.heading * self.ppu * 100, 1)

    def _draw_car(self, screen):
        # draw rectangle representing car
        angle = -self.heading.angle_to(Vector2(1, 0))
        car_corner_points = [
            Vector2(-self.length / 2, self.width / 2),
            Vector2(self.length / 2, self.width / 2),
            Vector2(self.length / 2, -self.width / 2),
            Vector2(-self.length / 2, -self.width / 2)
        ]
        car_corner_points = [p.rotate(angle) for p in car_corner_points]
        car_corner_points = [p * self.ppu for p in car_corner_points]
        car_corner_points = [p + self.position for p in car_corner_points]
        pg.draw.polygon(screen, (255, 255, 255), car_corner_points, 0)

        # indicate front of car
        pg.draw.line(screen, (255, 255, 0), self.position, self.position + self.heading * self.ppu * 0.1, 1)

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
            Vector2(self.length / 3, self.width / 2),
            Vector2(self.length / 3, -self.width / 2),
        ]

        tires = [p.rotate(angle) for p in tires]
        tires = [p * self.ppu for p in tires]
        tires = [p + self.position for p in tires]

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
            Vector2(-self.length / 3, self.width / 2),
            Vector2(-self.length / 3, -self.width / 2)
        ]
        tires = [p.rotate(angle) for p in tires]
        tires = [p * self.ppu for p in tires]
        tires = [p + self.position for p in tires]

        for tire in tires:
            points = [p + tire for p in tire_corner_points]
            pg.draw.polygon(screen, (255, 255, 255), points, 2)

    def _rotate_vector_about_point(self, vector, point, angle):
        """Rotate a vector about a point by a given angle in degrees."""
        vector = vector - point
        vector = vector.rotate(angle)
        vector = vector + point
        return vector

class SlamcarController:
    def __init__(self):
        pg.init()
        pg.display.set_caption("Slamcar Controller")
        self._print_boot_message()
        self.canvas_width = 800# // 2
        self.canvas_height = 520# // 2
        self.screen = pg.display.set_mode((self.canvas_width, self.canvas_height))
        self.clock = pg.time.Clock()
        self.ticks = 60
        self.exit = False
        self.ppu = 110
        current_path = os.path.dirname(__file__)
        icon = pg.image.load(current_path + '/icon.png')
        pg.display.set_icon(icon)



    def run(self):
        initial_position = (self.canvas_width // 2, self.canvas_height // 2)
        car = CarModel(*initial_position)

        while not self.exit:
            dt = self.clock.get_time() / 100
            self.screen.fill((0, 0, 0))

            # Update
            car.update(dt)

            # Draw
            self._draw_grid(self.screen)
            car.draw(self.screen, self.ppu)

            # Event handling
            self._EventHandling()

            self.clock.tick(self.ticks)
            pg.display.flip()


        pg.quit()

    def _print_boot_message(self):
        # using figlet
        f = Figlet(font='slant')
        print(f.renderText('SlamCar'))
        print("SlamCar Controller v0.1")

    def _draw_grid(self, screen):
        for x in range(0, self.canvas_width, self.ppu):
            pg.draw.line(screen, (50, 50, 50), (x, 0), (x, self.canvas_height))
        for y in range(0, self.canvas_height, self.ppu):
            pg.draw.line(screen, (50, 50, 50), (0, y), (self.canvas_width, y))

    def _EventHandling(self):
        # Event handling
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.exit = True
        # Keyboard handling
        pressed = pg.key.get_pressed()
        if pressed[pg.K_ESCAPE]:

            self.exit = True
        if pressed[pg.K_UP]:
            self.ppu += 5
        if pressed[pg.K_DOWN]:
            self.ppu -= 5


if __name__ == '__main__':
    slam_controller = SlamcarController()
    slam_controller.run()