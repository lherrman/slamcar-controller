import os
import time
import socket
import numpy as np
import cv2
from pyfiglet import Figlet
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg

from camera_stream_server import CameraStreamServer
from controll_stream_server import ControllStreamServer
from pyslam_con import PySlamCon
from base_model import CarModel
from ui_elements import UIButton, UIText, ConfigWindow, UIContainer
from config import Config as cfg


class SlamcarController:
    def __init__(self):
        pg.init()
        pg.display.set_caption("Slamcar Controller")
        self._print_boot_message()
        current_path = os.path.dirname(__file__)
        icon = pg.image.load(current_path + '/resources/icon.png')
        pg.display.set_icon(icon)
        self.canvas_width = 980
        self.canvas_height = 620
        self.screen = pg.display.set_mode((self.canvas_width, self.canvas_height))
        self.font = pg.font.SysFont("Helvetica", 16)
        self.clock = pg.time.Clock()
        self.ticks = 60
        self.exit = False

        self.ppu = 120 # pixels per unit 
        self.time_last_pressed = 0

        self.connected = False # Worker connected
        self.image_server = CameraStreamServer(port=cfg.get('image_stream_port'))
        self.controll_server = ControllStreamServer(port=cfg.get('controll_port'))
        # Controlls that get sent to Worker
        self.controlls = {
            'throttle': 0.0,
            'steering': 0.0
        }
        # UI elements
        self.ui_elements = []
        self._setup_ui()
        # Configuration window
        self.config_window_width = 250
        self._config_window_x_pos = self.canvas_width
        self._config_window = ConfigWindow((self._config_window_x_pos,30), (self.config_window_width,self.canvas_height-30))
        self._show_config = False

        self._show_camera_preview = False

        # Connected Worker Window
        self._connected_worker_window = None
        # self._connected_worker_window = UIContainer((0, 400), (150, 200))
        # self._connected_worker_window.add_element(UIText((0,0), "Worker 1", font_size=14))
        #     #worker_ip = self.controll_server.get_worker_ip()
        #     #self._connected_worker_window.add_element(UIText((0,20), f"{worker_ip}", font_size=14))
        # self.ui_elements.append(self._connected_worker_window)
        # PySlam Connection
        self.pyslam = PySlamCon(r'\\wsl.localhost\Ubuntu\home\user\slamcar\pyslam\videos\images')

    def run(self):
        initial_position = (3, 3)
        self.car = CarModel(*initial_position)
        self.image_server.start()
        self.controll_server.start()

        while not self.exit:            
            dt = self.clock.get_time() / 100
            self.screen.fill((30, 30, 30))

            # Draw connected worker window
            self._draw_connected_worker_window()

            # Update
            self.car.update(dt)
            self._update_controlls()
            # Handle events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.exit = True
                if event.type == pg.USEREVENT:
                    # Monitor config changes
                    if event.action == 'config_changed':
                        self.car.load_parameters()
                    if event.action == 'remote_config_changed':
                        self.controll_server.send_config(cfg.get('car_parameters'))
                if event.type == pg.MOUSEBUTTONDOWN:
                    # Zoom in and out with mouse wheel
                    if event.button == 4:
                        self.ppu += 10
                    elif event.button == 5:
                        self.ppu -= 10

                for element in self.ui_elements:
                    element.update(event)

                self._config_window.update(event)
            
            # Draw
            self.car.draw(self.screen, self.ppu)  # draw car
            self._draw_gui(self.screen)           # draw gui
            for element in self.ui_elements:
                element.draw(self.screen)
            
            # Draw configuration window with slide in animation
            self._draw_configuration()

            # Show image preview
            self._reviece_images()

            self.clock.tick(self.ticks)
            pg.display.flip()
        
            # Event handling
            self._EventHandling()

                
        cv2.destroyAllWindows()
        self.image_server.close()
        pg.quit()


    def _send_image_to_slam(self, image):
        self.pyslam.put_image(image)

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
        
    def _toggle_camera_preview(self):
        self._show_camera_preview = not self._show_camera_preview

    def _toggle_configuration_window(self):
        self._show_config = not self._show_config

    def _draw_gui(self, screen):
        self._draw_hbar(screen, pos='top', height=30, color=(37, 37, 37))

        self._draw_connection_status_text(screen)
        self._draw_configuration()

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

    def _draw_connected_worker_window(self):    
        if self._connected_worker_window is None and self.connected:   
            self._connected_worker_window = UIContainer((20, 50), (150, 160))
            self._connected_worker_window.add_element(UIText((40,20), "Worker 1", font_size=20))
            self._connected_worker_window.add_element(UIButton((10,50), (130, 30), "Show Camera", self._toggle_camera_preview))
            self._connected_worker_window.add_element(UIButton((10,80), (130, 30), "Open Image Folder", self._open_pyslam_image_folder))
            self._connected_worker_window.add_element(UIButton((10,110), (130, 30), "Reinitialize", self._config_window.reinit_worker()))
            self.ui_elements.append(self._connected_worker_window)

    def _draw_configuration(self):
        if self._show_config: 
            config_window_target_x_pos = (self.canvas_width - self.config_window_width)
        else:
            config_window_target_x_pos = self.canvas_width
        if abs(config_window_target_x_pos - self._config_window_x_pos) > 1:
            self._config_window.update(pg.event.Event(pg.USEREVENT, action='None'))
        self._config_window_x_pos = 0.1 * config_window_target_x_pos + 0.9 * self._config_window_x_pos
        self._config_window.move_to(self._config_window_x_pos, 30)
        self._config_window.draw(self.screen)

    def _open_pyslam_image_folder(self):
        os.startfile(self.pyslam.image_dir)

    def _reviece_images(self):
        '''Show camera preview in a separate window'''
        window_name = 'SlamCar Camera'
        if not hasattr(self, '_image_preview_last_image'):
            self._image_preview_last_image = np.zeros((480, 640, 3), np.uint8)

        if not hasattr(self, 'i_counter'):
            self.i_counter = 0

        image = self.image_server.receive_image()
        if image is not None:
            self.connected = True
            self._image_preview_last_image = image
      
            self.i_counter += 1
            if self.i_counter % 2 == 0:
                self._send_image_to_slam(image)
                
        if self.connected and self._show_camera_preview:
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
            if self.ppu < 10:
                self.ppu = 10

        # debounce key presses
        if time.time() - self.time_last_pressed > 0.2:

            if pressed[pg.K_g]:
                self.time_last_pressed = time.time()
                self.draw_grid = not self.draw_grid

            if pressed[pg.K_t]:
                self.time_last_pressed = time.time()
                self.car.draw_track_projection = not self.car.draw_track_projection

    def _update_controlls(self):
        self.controlls['steering'] = self.car.steering / cfg.get('max_steering')
        self.controlls['throttle'] = self.car.velocity_magnitude / cfg.get('max_velocity')

        with self.controll_server.controll_lock:
            self.controll_server.controlls['steering'] = self.controlls['steering']
            self.controll_server.controlls['throttle'] = self.controlls['throttle']

        return
    

if __name__ == '__main__':
    slam_controller = SlamcarController()
    slam_controller.run()


