import os
import time
import socket
import numpy as np
import cv2
from pyfiglet import Figlet
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg

from camera_stream_server import CameraStreamServer
from base_model import CarModel
from ui import UIButton, UIText
import config as cfg


class SlamcarController:
    def __init__(self):
        pg.init()
        pg.display.set_caption("Slamcar Controller")
        self._print_boot_message()
        current_path = os.path.dirname(__file__)
        icon = pg.image.load(current_path + '/resources/icon.png')
        pg.display.set_icon(icon)
        self.canvas_width = 800
        self.canvas_height = 520
        self.screen = pg.display.set_mode((self.canvas_width, self.canvas_height))
        self.font = pg.font.SysFont("Helvetica", 16)
        self.clock = pg.time.Clock()
        self.ticks = 60
        self.exit = False

        self.ppu = 120 # pixels per unit
        self.draw_grid = True
        self.time_last_pressed = 0

        self.connected = False
        self.image_receiver = CameraStreamServer(port=cfg.CAMERA_PORT)

        self.ui_elements = []
        self._setup_ui()

    def run(self):
        initial_position = (3, 3)
        self.car = CarModel(*initial_position)
        self.image_receiver.start()

        while not self.exit:            
            dt = self.clock.get_time() / 100
            self.screen.fill((0, 0, 0))

            # Update
            self.car.update(dt)

            # Draw
            if self.draw_grid: self._draw_grid(self.screen) # draw grid
            self.car.draw(self.screen, self.ppu)            # draw car
            self._draw_gui(self.screen)                     # draw gui
            for element in self.ui_elements:
                element.update(pg.event.poll())
                element.draw(self.screen)

            # Show image preview
            self._show_image_preview()

            self.clock.tick(self.ticks)
            pg.display.flip()
        
            # Event handling
            self._EventHandling()
                
        cv2.destroyAllWindows()
        self.image_receiver.close()
        pg.quit()

    def _print_boot_message(self):
        f = Figlet(font='slant')
        print(f.renderText('SlamCar'))
        print("SlamCar Controller")

    def _setup_ui(self):
        # Configuration button
        self.ui_elements.append(UIButton((self.canvas_width - 100, 0), 
                                    (100, 30), "configuration", 
                                    self._toggle_configuration_window))
        # Display local IP address
        local_ip = self._get_local_ip()
        self.ui_elements.append(UIText((10, self.canvas_height-20),
                                    f"{local_ip}", font_size=14))

    def _toggle_configuration_window(self):
        ...

    def _draw_grid(self, screen):
        for x in range(0, self.canvas_width, self.ppu):
            pg.draw.line(screen, (50, 50, 50), (x, 0), (x, self.canvas_height))
        for y in range(0, self.canvas_height, self.ppu):
            pg.draw.line(screen, (50, 50, 50), (0, y), (self.canvas_width, y))

    def _draw_gui(self, screen):
        self._draw_hbar(screen, pos='top', height=30, color=(0, 0, 0))

        self._draw_connection_status_text(screen)
        self._draw_configuration(screen)

    def _draw_hbar(self, screen, pos='top', height=30, color=(0, 0, 0)):
        '''Draw a horizontal bar at the top or bottom of the screen'''
        if pos == 'top':
            pg.draw.rect(screen, color, (0, 0, self.canvas_width, height))
        elif pos == 'bottom':
            pg.draw.rect(screen, color, (0, self.canvas_height - height, self.canvas_width, height))

    def _draw_connection_status_text(self, screen):
        # initialize and update helper variables
        if not hasattr(self, '_time_buffer'):
            self._time_buffer = time.time()
        if not hasattr(self, '_gui_connection_text_helper'):
            self._gui_connection_text_helper = 0
        if time.time() - self._time_buffer > 1:
            self._time_buffer = time.time()
            self._gui_connection_text_helper = ((self._gui_connection_text_helper + 1) % 3 )

        position = (10, 7)
        if self.connected:
            text = self.font.render(f"connected", True, (255, 255, 255))
            screen.blit(text, position)
        else:   
            text = self.font.render(f"waiting for connection " + 
                               "."*(self._gui_connection_text_helper+1), True, (255, 255, 255))
            screen.blit(text, position)
            

    def _draw_configuration(self, screen):
        ...

    def _show_image_preview(self):
        '''Show camera preview in a separate window'''
        window_name = 'SlamCar Camera'
        if not hasattr(self, '_image_preview_last_image'):
            self._image_preview_last_image = np.zeros((480, 640, 3), np.uint8)
            
        image = self.image_receiver.receive_image()
        if image is not None:
            self.connected = True
            cv2.imshow(window_name, image)
            self._image_preview_last_image = image
        if self.connected:
            cv2.imshow(window_name, self._image_preview_last_image)

    def _get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('192.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP
    
    def _EventHandling(self):
        # Event handling
        for event in pg.event.get():
            if event.type == pg.QUIT:
                print("Quit")
                self.exit = True
            
        # Keyboard handling
        pressed = pg.key.get_pressed()

        # Exit
        if pressed[pg.K_ESCAPE]:
            self.exit = True

        # Camera zoom
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

    def get_basemodel_state(self):
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


