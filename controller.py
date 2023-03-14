import os
import numpy as np
import threading
import time
from pyfiglet import Figlet
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg
from pygame.math import Vector2
from base_model import CarModel

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
        icon = pg.image.load(current_path + 'resources/icon.png')
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