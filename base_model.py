import time
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
    def __init__(self, x, y, angle=0.0, length=0.4, width=0.2):
        self.MAX_VELOCITY = 7.0
        self.ACCELERATION_SPEED = 2 # meters per second
        self.LENGTH = length        # length of the car in meters
        self.WIDTH = width          # width of the car in meters
        self.STEERING_SPEED = 10.0  # degrees per second
        self.MAX_STEERING = 30.0    # degrees

        self.position = Vector2(x, y)                # position in meters
        self.heading = Vector2(0, -1).normalize()    # heading towards the front of the car
        self.velocity = Vector2(0.0, 0.0)            # velocity in meters per second
        self.velocity_magnitude = 0.0                # velocity magnitude in meters per second
        self.steering = 0.0                          # tire angle in degrees
        self.steering_radius = 0.0                   # radius of the circle the car is moving on
        self.steering_rotation_point = Vector2(0, 0) # point around which the car is rotating
        self.rotation_position = -0.5                # 1.0 = front, -1.0 = back

        self.magic_number = 0.014 # temporary bug with velocity calculation

        self.ppu = 64           # pixels per unit
        self.draw_track = False # draw the track the car is moving on

    def update(self, dt):
        self._update_position(dt)
        self._update_inputs(dt)
        self._calculate_steering_rotation_point()

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
            return self.LENGTH / math.tan(math.radians(self.steering))
        
    def _update_steering(self, left, right, dt):
        if left:
            self.steering = max(-self.MAX_STEERING, self.steering - self.STEERING_SPEED * dt)

        if right:
            self.steering = min(self.MAX_STEERING, self.steering + self.STEERING_SPEED * dt)

        # If neither is pressed, reduce steering to 0
        # back_steer_factor determines how fast the steering will go back to 0
        back_steer_factor = 2
        if not left and not right:
            if self.steering > 0:
                self.steering = max(0, self.steering - self.STEERING_SPEED * dt * back_steer_factor)
            else:
                self.steering = min(0, self.steering + self.STEERING_SPEED * dt * back_steer_factor)
        
    def _update_velocity(self, up, down, dt):
        if up:
            self.velocity_magnitude = min(self.MAX_VELOCITY, self.velocity_magnitude + self.ACCELERATION_SPEED * dt)
        if down:
            self.velocity_magnitude = max(-self.MAX_VELOCITY, self.velocity_magnitude - self.ACCELERATION_SPEED * dt)

        # If neither is pressed, reduce velocity to 0
        if not up and not down:
            if self.velocity_magnitude > 0:
                self.velocity_magnitude = max(0, self.velocity_magnitude - self.ACCELERATION_SPEED * dt)
            else:
                self.velocity_magnitude = min(0, self.velocity_magnitude + self.ACCELERATION_SPEED * dt)
        
    def _calculate_steering_rotation_point(self):
        angle = -self.heading.angle_to(Vector2(1, 0))
        self.steering_rotation_point = Vector2(0, self.steering_radius)
        self.steering_rotation_point = self.steering_rotation_point.rotate(angle)
        self.steering_rotation_point += self.rotation_position * (self.heading.normalize()  * self.LENGTH / 2 )
        #self.steering_rotation_point *= self.ppu
        self.steering_rotation_point += self.position

    def draw(self, screen, ppu):
        self.ppu = ppu
        if self.draw_track: self._draw_steering_radius(screen, True)
        self._draw_tires(screen)
        self._draw_car(screen)

    def _draw_steering_radius(self, screen, draw_wide_track=False):
        # Draw steering radius
        color_track = (0, 10, 10)
        color_line = (0, 60, 60)
        width = int(self.WIDTH * self.ppu)
        
        if self.steering_radius > 0:
            if draw_wide_track:
                pg.draw.circle(screen, color_track, self.steering_rotation_point * self.ppu, self.steering_radius * self.ppu + width //2, width)
            pg.draw.circle(screen, color_line, self.steering_rotation_point  * self.ppu, self.steering_radius * self.ppu, 1)
        elif self.steering_radius < 0: 
            if draw_wide_track:
                pg.draw.circle(screen, color_track, self.steering_rotation_point  * self.ppu, -self.steering_radius * self.ppu + width // 2, width)
            pg.draw.circle(screen, color_line, self.steering_rotation_point  * self.ppu, -self.steering_radius * self.ppu, 1)
        else:
            if draw_wide_track:
                pg.draw.line(screen, color_track, self.position * self.ppu - self.heading * self.ppu * 100, self.position * self.ppu + self.heading * self.ppu * 100, width)
            pg.draw.line(screen, color_line, self.position * self.ppu - self.heading * self.ppu * 100, self.position * self.ppu + self.heading * self.ppu * 100, 1)

    def _draw_car(self, screen):
        # draw rectangle representing car
        angle = -self.heading.angle_to(Vector2(1, 0))
        car_corner_points = [
            Vector2(-self.LENGTH / 2, self.WIDTH / 2),
            Vector2(self.LENGTH / 2, self.WIDTH / 2),
            Vector2(self.LENGTH / 2, -self.WIDTH / 2),
            Vector2(-self.LENGTH / 2, -self.WIDTH / 2)
        ]
        car_corner_points = [p.rotate(angle) for p in car_corner_points]
        car_corner_points = [p + self.position for p in car_corner_points]
        car_corner_points = [p * self.ppu for p in car_corner_points]
        pg.draw.polygon(screen, (255, 255, 255), car_corner_points, 0)

        # indicate front of car
        #pg.draw.line(screen, (255, 255, 0), self.position *  self.ppu, (self.position + self.heading) * self.ppu * 0.1, 1)

    def _draw_tires(self, screen):
        # Draw tires
        angle = -self.heading.angle_to(Vector2(1, 0))
        tire_width = self.WIDTH / 4
        tire_length = self.LENGTH / 4

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
            Vector2(self.LENGTH / 3, self.WIDTH / 2),
            Vector2(self.LENGTH / 3, -self.WIDTH / 2),
        ]

        tires = [p.rotate(angle) for p in tires]
        tires = [p + self.position for p in tires]
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
            Vector2(-self.LENGTH / 3, self.WIDTH / 2),
            Vector2(-self.LENGTH / 3, -self.WIDTH / 2)
        ]
        tires = [p.rotate(angle) for p in tires]
        tires = [p + self.position for p in tires]
        tires = [p * self.ppu for p in tires]

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
        self.canvas_width = 800
        self.canvas_height = 520
        self.screen = pg.display.set_mode((self.canvas_width, self.canvas_height))
        self.clock = pg.time.Clock()
        self.ticks = 60
        self.exit = False
        self.ppu = 120
        self.draw_grid = True
        current_path = os.path.dirname(__file__)
        icon = pg.image.load(current_path + '/icon.png')
        pg.display.set_icon(icon)
        self.time_last_pressed = 0

        self.connected = False

        self.gui_connection_helper = 0

    def run(self):
        initial_position = (3, 3)
        self.car = CarModel(*initial_position)

        while not self.exit:            
            dt = self.clock.get_time() / 100
            self.screen.fill((0, 0, 0))

            # Update
            self.car.update(dt)

            # Draw
            if self.draw_grid: self._draw_grid(self.screen)
            self.car.draw(self.screen, self.ppu)

            # GUI
            self._draw_gui(self.screen)

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

    def _draw_gui(self, screen):
        # draw black title bar
        titlebar_height = 30
        titlebar_color = (0, 0, 0)
        pg.draw.rect(screen, titlebar_color, (0, 0, self.canvas_width, titlebar_height))

        self._draw_connection_status_text(screen)
        self._draw_configuration(screen)

    def _draw_connection_status_text(self, screen):
        # initialize and update helper variables
        if not hasattr(self, '_time_buffer'):
            self._time_buffer = time.time()
        if not hasattr(self, '_gui_connection_text_helper'):
            self._gui_connection_text_helper = 0
        if time.time() - self._time_buffer > 1:
            self._time_buffer = time.time()
            self._gui_connection_text_helper = ((self._gui_connection_text_helper + 1) % 3 )

        # draw text waiting for connection
        if self.connected:
            font = pg.font.SysFont('Arial', 15)
            text = font.render(f"connected", True, (255, 255, 255))
            screen.blit(text, (10, 7))
        else:   
            font = pg.font.SysFont('Arial', 15)
            text = font.render(f"waiting for connection " + "."*(self._gui_connection_text_helper+1), True, (255, 255, 255))
            screen.blit(text, (10, 7))

    def _draw_configuration(self, screen):
        button_width = 100
        button_height = 30
        button_color = (0, 0, 0)

        # draw button with hover effect
        mouse = pg.mouse.get_pos()
        click = pg.mouse.get_pressed()
        if self.canvas_width - button_width < mouse[0] < self.canvas_width and 0 < mouse[1] < button_height:
            if click[0] == 1:
                print("clicked")
            button_color = (30, 30, 30)
        pg.draw.rect(screen, button_color, (self.canvas_width - button_width, 0, button_width, button_height))

        # draw text on button
        font = pg.font.SysFont('Arial', 15)
        text = font.render(f"configuration", True, (255, 255, 255))
        screen.blit(text, (self.canvas_width - button_width + 15, 7))


    def _EventHandling(self):
        # Event handling
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.exit = True
        # Keyboard handling
        pressed = pg.key.get_pressed()

        # Exit
        if pressed[pg.K_ESCAPE]:

        # Camera zoom
            self.exit = True
        if pressed[pg.K_UP]:
            self.ppu += 5
        if pressed[pg.K_DOWN]:
            self.ppu -= 5
            if self.ppu < 1:
                self.ppu = 1

        # debounce key presses
        if time.time() - self.time_last_pressed > 0.2:

            if pressed[pg.K_g]:
                self.time_last_pressed = time.time()
                self.draw_grid = not self.draw_grid

            if pressed[pg.K_t]:
                self.time_last_pressed = time.time()
                self.car.draw_track = not self.car.draw_track

    def get_state(self):
        state = {
            'position': self.car.position,
            'heading': self.car.heading,
            'velocity': self.car.velocity,
            'steering_angle': self.car.steering,
        }
        return state
    

if __name__ == '__main__':
    slam_controller = SlamcarController()
    slam_controller.run()