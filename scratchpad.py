import sys
import numpy as np
import cv2
import logging
import os
import math
import pygame
from pygame.math import Vector2



class Car:
    def __init__(self, x, y, angle=0.0, length=0.4, width=0.2, max_steering=30, max_acceleration=30.0):
        self.position = Vector2(x, y)
        self.heading = Vector2(-1, -2).normalize()
        self.velocity = Vector2(0.0, 0.0)
        self.velocity_magnitude = 0.0

        self.length = length
        self.width = width

        self.max_steering = max_steering
        self.steering = 0.0 # degrees
        self.steering_radius = 0.0 # meters

        self.ppu = 64 # pixels per unit (meters)

    def update(self, dt):
        self._update_position(dt)
        self._update_inputs(dt)

    def _update_position(self, dt):
        velocity_factor = 2.6
        if self.steering == 0:
            self.velocity = self.heading * self.velocity_magnitude
            self.position += self.velocity * dt * velocity_factor
        else:
            # rotation_angle = self.velocity_magnitude / self.steering_radius * dt
            # self.heading.rotate_ip(rotation_angle)
            # self.position += self.heading * self.velocity_magnitude * dt * velocity_factor
            rotation_angle = self.velocity_magnitude / self.steering_radius * dt
            self.heading.rotate_ip(rotation_angle)
            self.position += self.heading * self.velocity_magnitude * dt * velocity_factor
            






    def _update_inputs(self, dt):
        pressed = pygame.key.get_pressed()

        # Steering
        steering_speed = 3
        if pressed[pygame.K_a]:
            self.steering = max(-self.max_steering, self.steering - steering_speed * dt)

        if pressed[pygame.K_d]:
            self.steering = min(self.max_steering, self.steering + steering_speed * dt)
        # If neither A or D is pressed, reduce steering to 0
        if not pressed[pygame.K_a] and not pressed[pygame.K_d]:
            if self.steering > 0:
                self.steering = max(0, self.steering - steering_speed * dt)
            else:
                self.steering = min(0, self.steering + steering_speed * dt)

        self.steering_radius = self._calculate_steering_radius()

        # Velocity
        velocity_speed = 0.3
        if pressed[pygame.K_w]:
            self.velocity_magnitude = min(1, self.velocity_magnitude + velocity_speed * dt)

        if pressed[pygame.K_s]:
            self.velocity_magnitude = max(-1, self.velocity_magnitude - velocity_speed * dt)

        # If neither W or S is pressed, reduce velocity to 0
        if not pressed[pygame.K_w] and not pressed[pygame.K_s]:
            if self.velocity_magnitude > 0:
                self.velocity_magnitude = max(0, self.velocity_magnitude - velocity_speed * dt)
            else:
                self.velocity_magnitude = min(0, self.velocity_magnitude + velocity_speed * dt)
        
        print(self.velocity_magnitude)


    def _calculate_steering_radius(self):
        if self.steering == 0:
            return 0
        else:
            return self.length / math.tan(math.radians(self.steering))
        
    def draw(self, screen, ppu):
        self.ppu = ppu
        # Draw car
        #self.heading.rotate_ip(self.steering*0.02)

        # get angle from heading
        angle = -self.heading.angle_to(Vector2(1, 0))

        self._draw_steering_radius(screen)
        self._draw_tires(screen)
        self._draw_car(screen)

    def _draw_steering_radius(self, screen):
        # Draw steering radius
        angle = -self.heading.angle_to(Vector2(1, 0))
        color_track = (0, 0, 30)
        color_line = (0, 0, 255)
        width = int(self.width * self.ppu)
        if self.steering_radius > 0:
            steering_rotation_point = Vector2(0, self.steering_radius)
            steering_rotation_point = steering_rotation_point.rotate(angle)
            steering_rotation_point = steering_rotation_point * self.ppu
            steering_rotation_point = steering_rotation_point + self.position
            pygame.draw.circle(screen, color_track, steering_rotation_point, self.steering_radius * self.ppu + width //2, width)
            pygame.draw.circle(screen, color_line, steering_rotation_point, self.steering_radius * self.ppu, 1)
        elif self.steering_radius < 0: 
            steering_rotation_point = Vector2(0, self.steering_radius)
            steering_rotation_point = steering_rotation_point.rotate(angle)
            steering_rotation_point = steering_rotation_point * self.ppu
            steering_rotation_point = steering_rotation_point + self.position
            pygame.draw.circle(screen, color_track, steering_rotation_point, -self.steering_radius * self.ppu + width // 2, width)
            pygame.draw.circle(screen, color_line, steering_rotation_point, -self.steering_radius * self.ppu, 1)

        else:
            pygame.draw.line(screen, color_track, self.position - self.heading * self.ppu * 100, self.position + self.heading * self.ppu * 100, width)
            pygame.draw.line(screen, color_line, self.position - self.heading * self.ppu * 100, self.position + self.heading * self.ppu * 100, 1)


    def _draw_car(self, screen):
        # Draw car
        #self.heading.rotate_ip(self.steering*0.1)

        # get angle from heading
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
        pygame.draw.polygon(screen, (255, 255, 255), car_corner_points, 0)

        # indicate front of car
        pygame.draw.line(screen, (255, 255, 0), self.position, self.position + self.heading * self.ppu * 0.1, 1)

    def _draw_tires(self, screen):
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
            pygame.draw.polygon(screen, (255, 255, 255), points, 2)

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
            pygame.draw.polygon(screen, (255, 255, 255), points, 2)

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Slamcar Controller")
        self.canvas_width = 1080# // 2
        self.canvas_height = 640# // 2
        self.screen = pygame.display.set_mode((self.canvas_width, self.canvas_height))
        self.clock = pygame.time.Clock()
        self.ticks = 60
        self.exit = False
        self.ppu = 150
        current_path = os.path.dirname(__file__)
        icon = pygame.image.load(current_path + '/icon.png')
        pygame.display.set_icon(icon)

    def run(self):

        car = Car(self.canvas_width // 2, self.canvas_height // 2)

        while not self.exit:
            dt = self.clock.get_time() / 50
            self.screen.fill((0, 0, 0))


            # Update
            car.update(dt)

            # Draw
            self._draw_grid(self.screen)
            car.draw(self.screen, self.ppu)

            # Event handling
            self._EventHandling()

            self.clock.tick(self.ticks)
            pygame.display.flip()


        pygame.quit()

    def _draw_grid(self, screen):
        for x in range(0, self.canvas_width, self.ppu):
            pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, self.canvas_height))
        for y in range(0, self.canvas_height, self.ppu):
            pygame.draw.line(screen, (50, 50, 50), (0, y), (self.canvas_width, y))

    def _EventHandling(self):
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.exit = True
        # Keyboard handling
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_ESCAPE]:
            self.exit = True


game = Game()
game.run()