import pygame as pg


class UIElement():
    def __init__(self, position):
        self.position = position
        self.mouse_over = False

    def update(self, event):
        ...

    def draw(self, screen):
        ...

class UIContainer(UIElement):
    def __init__(self, position, size, bg_color=(20,20,20)):
        super().__init__(position)
        self.size = size
        self.bg_color = bg_color
        self.elements = []

    def update(self, event):
        self.rect = pg.Rect(self.position, self.size)
        for element in self.elements:
            element.update(event)

    def add_element(self, element: UIElement):
        element.position = (element.position[0] + self.position[0], element.position[1] + self.position[1])
        self.elements.append(element)

    def draw(self, screen):
        # create a surface from the rect
        self.image = pg.Surface(self.rect.size)
        # fill the surface with the color
        self.image.fill(self.bg_color)
        # draw the surface on the screen
        screen.blit(self.image, self.rect)

        for element in self.elements:
            element.draw(screen)

    def move_to(self, x, y):
        self._move(x - self.position[0], y - self.position[1])

    def _move(self, x, y):
        self.position = (self.position[0] + x, self.position[1] + y)
        for element in self.elements:
            element.position = (element.position[0] + x, element.position[1] + y)


class UIButton(UIElement):
    def __init__(self, position, size, text, action=None, args=None, font_size= 16, text_color= (255,255,255), bg_color=(0,0,0), bg_color_hover=(50,50,50)):
        super().__init__(position)
        self._action = action
        self._set_args(args)
        self._text = text
        self.size = size
        self._font = pg.font.SysFont("Helvetica ", font_size)
        self._bg_color = bg_color
        self._bg_color_hover = bg_color_hover
        self._bg_color_active = self._bg_color
        self._text_color = text_color
        self.center_position = (position[0] + size[0] // 2, position[1] + size[1] // 2)

    def _set_args(self, args):
        if args is None:
            args = []
        if not isinstance(args, list):
            args = [args]
        self._args = args

    def update(self, event):
        self.text_img = self._font.render(self._text, True, self._text_color, self._bg_color_active)
        self.rect = pg.Rect(self.position, self.size)
        
        # Handle hover events
        if event.type == pg.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self._bg_color_active = self._bg_color_hover
            else:
                self._bg_color_active = self._bg_color

        # Handle click events
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if self._action is not None:
                    self._action(*self._args)

    def draw(self, screen):
        # create a surface from the rect
        self.image = pg.Surface(self.rect.size)
        # fill the surface with the color
        self.image.fill(self._bg_color_active)
        # draw the text on the surface
        self.image.blit(self.text_img, (self.rect.width // 2 - self.text_img.get_width() // 2, self.rect.height // 2 - self.text_img.get_height() // 2))
        # draw the surface on the screen
        screen.blit(self.image, self.rect)

class UIText(UIElement):
    def __init__(self, position, text, font_size= 16, text_color= (255,255,255), bg_color=None):
        super().__init__(position)
        self._text = text
        self._font = pg.font.SysFont("Helvetica ", font_size)
        self._bg_color = bg_color
        self._text_color = text_color

    def update(self, event):
        self.image = self._font.render(self._text, True, self._text_color, self._bg_color)
        self.center_position = (self.position[0] + self.image.get_width() // 2, self.position[1] + self.image.get_height() // 2)
        self.rect = self.image.get_rect(center=self.center_position)

    def update_text(self, text):
        self._text = text

    def draw(self, screen):
        screen.blit(self.image, self.rect)

class UITextInput(UIElement):
    def __init__(self, position, size, text, font_size= 16, text_color= (255,255,255), bg_color=(0,0,0), bg_color_hover=(50,50,50)):
        super().__init__(position)
        self._text = text
        self.size = size
        self._font = pg.font.SysFont("Helvetica ", font_size)
        self._bg_color = bg_color
        self._bg_color_hover = bg_color_hover
        self._bg_color_active = self._bg_color
        self._text_color = text_color
        self.center_position = (position[0] + size[0] // 2, position[1] + size[1] // 2)
        self._selected = False

    def update(self, event):
        self.text_img = self._font.render(self._text, True, self._text_color, self._bg_color_active)
        self.rect = pg.Rect(self.position, self.size)
        
        # Handle hover events
        if event.type == pg.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self._bg_color_active = self._bg_color_hover
            else:
                self._bg_color_active = self._bg_color

        # Handle click events
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self._selected = not self._selected
            else:
                self._selected = False

        # Handle text input
        if event.type == pg.KEYDOWN:
            if self._selected:
                if event.key == pg.K_RETURN:
                    print(self._text)
                elif event.key == pg.K_BACKSPACE:
                    self._text = self._text[:-1]
                else:
                    self._text += event.unicode

    def draw(self, screen):
        # create a surface from the rect
        self.image = pg.Surface(self.rect.size)
        # fill the surface with the color
        self.image.fill(self._bg_color_active)
        # draw the text on the surface
        self.image.blit(self.text_img, (self.rect.width // 2 - self.text_img.get_width() // 2, self.rect.height // 2 - self.text_img.get_height() // 2))
        # draw the surface on the screen
        screen.blit(self.image, self.rect)

import time
class UIJsonValue(UIElement):
    '''
    A UI element that displays a value from a json file and allows to change it
    '''
    def __init__(self, position, size, json_key:str, font_size: int= 16, 
                 text_color= (255,255,255), 
                 bg_color=(0,0,0), 
                 bg_color_hover=(50,50,50),
                 bg_color_selected=(60,60,70)):
        
        super().__init__(position)
        self._json_value = self.read_json(json_key)
        self._json_key = json_key
        self.size = size
        self._font = pg.font.SysFont("Helvetica ", font_size)
        self._bg_color = bg_color
        self._bg_color_hover = bg_color_hover
        self._bg_color_selected = bg_color_selected
        self._bg_color_active = self._bg_color 
        self._text_color = text_color
        self.center_position = (position[0] + size[0] // 2, position[1] + size[1] // 2)
        self._selected = False
        self._hovered = False
        self.text_buffer = str(self._json_value)
        self.cursor_time_since_last_blink = time.time()
        self.cursor_blink_rate = 0.5
        self.cursor_visible = True
        self.cursor_position = len(self.text_buffer)

    def update(self, event):
        split_percent = 0.7
        # Left side of the UI element (variable name)
        varaiable_name = self._json_key.replace("_", " ")
        #varaiable_name = " ".join([word.capitalize() for word in varaiable_name.split(" ")])
        self.text_img_key = self._font.render(varaiable_name, True, self._text_color, self._bg_color)
        position_key = (self.position[0], self.position[1])
        size_key = (self.size[0] * split_percent, self.size[1])
        self.rect_key = pg.Rect(position_key, size_key)
 
        if self._selected:
            value = self.text_buffer[:self.cursor_position] + "|" + self.text_buffer[self.cursor_position:]
        else:
            value = self.text_buffer
        self.text_img_value = self._font.render(value, True, self._text_color, self._bg_color_active)
        position_value = (self.position[0] + self.size[0] * split_percent, self.position[1])
        size_value = (self.size[0] * (1 - split_percent), self.size[1])
        self.rect_value = pg.Rect(position_value, size_value)
        
        # Handle hover events
        if event.type == pg.MOUSEMOTION:
            if self.rect_value.collidepoint(event.pos):
                self._hovered = True
            else:
                self._hovered = False

        if self._selected:
            self._bg_color_active = self._bg_color_selected
        elif self._hovered:
            self._bg_color_active = self._bg_color_hover
        else:
            self._bg_color_active = self._bg_color

        # Handle click events
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.rect_value.collidepoint(event.pos):
                self._selected = not self._selected
                if self._selected:
                    self.text_buffer = value
                if not self._selected:
                    self.write_json(self._json_key, self.text_buffer)
                    self._bg_color_active = self._bg_color
            else:
                self._selected = False
                
        # Handle text input
        if event.type == pg.KEYDOWN:
            if self._selected:
                # Move cursor
                if event.key == pg.K_LEFT:
                    self.cursor_position = max(0, self.cursor_position - 1)
                elif event.key == pg.K_RIGHT:
                    self.cursor_position = min(len(self.text_buffer), self.cursor_position + 1)
                # On enter, write to json file and post an event to notify the main loop
                elif event.key == pg.K_RETURN:
                    self._selected = False
                    self.write_json(self._json_key, self.text_buffer)
                    self._bg_color_active = self._bg_color
                    pg.event.post(pg.event.Event(pg.USEREVENT, {"action": "config_changed"}))
                # Delete text at cursor
                elif event.key == pg.K_BACKSPACE:
                    self.text_buffer = self.text_buffer[:max(0, self.cursor_position - 1)] + self.text_buffer[self.cursor_position:]
                    self.cursor_position = max(0, self.cursor_position - 1)
                # write text at cursor
                else:
                    self.text_buffer = self.text_buffer[:self.cursor_position] + event.unicode + self.text_buffer[self.cursor_position:]
                    self.cursor_position += 1

    def draw(self, screen):
        self.image1 = pg.Surface(self.rect_value.size)
        self.image1.fill(self._bg_color_active)
        self.image1.blit(self.text_img_value,
                         (self.rect_value.width // 2 - self.text_img_value.get_width() // 2,
                           self.rect_value.height // 2 - self.text_img_value.get_height() // 2))
        screen.blit(self.image1, self.rect_value)

        self.image2 = pg.Surface(self.rect_key.size)
        self.image2.fill(self._bg_color)
        self.image2.blit(self.text_img_key, 
                        (self.rect_key.width // 2 - self.text_img_key.get_width() // 2,
                          self.rect_key.height // 2 - self.text_img_key.get_height() // 2))
        screen.blit(self.image2, self.rect_key)

    def read_json(self, variable):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                return config[variable]
        except:
            raise ValueError(f"{variable} not found in config.json")
        
    def write_json(self, variable, value):
        value = value.strip()
        try:
            if value.endswith("."):
                value = str(value)
            elif '.' in value:
                value = float(value)
            else:
                value = int(value)
        except:
            return None
        
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                config[variable] = value
            with open("config.json", "w") as f:
                json.dump(config, f, indent=2)
        except:
            return None
        
    def increase_config(self, variable, value):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                config[variable] += value
                print(config[variable])
            with open("config.json", "w") as f:
                json.dump(config, f, indent=2)
        except:
            return None


import json
class ConfigWindow(UIContainer):
    def __init__(self, position, size=(300,600), bg_color=(0,0,0)):
        super().__init__(position, size, bg_color)

        spacing_top = 20
        spacing_sides = 10
        spacing_between = 10
        elements_height = 25
        elements_width = self.size[0] - 2 * spacing_sides

        keys_in_config = [key for key in json.load(open("config.json", "r"))]

        elements = [UIJsonValue((0, 0), (0, 0), key) for key in keys_in_config]

        spacing_between = 5
        for i, element in enumerate(elements):
            element.position = (spacing_sides,spacing_top +  i * (elements_height + spacing_between))
            element.size = (elements_width, elements_height)
            self.add_element(element)

    def read_json(self, variable):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                return config[variable]
        except:
            return None
        
    def write_json(self, variable, value):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                config[variable] = value
            with open("config.json", "w") as f:
                json.dump(config, f, indent=2)
        except:
            return None
        
    def increase_config(self, variable, value):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                config[variable] += value
                print(config[variable])
            with open("config.json", "w") as f:
                json.dump(config, f, indent=2)
        except:
            return None


if __name__ == "__main__":
    pg.init()
    screen = pg.display.set_mode((800, 600))
    clock = pg.time.Clock()
    done = False

    config_window = ConfigWindow((100, 0))
    
    while not done:
        screen.fill((0,0,0))
        for event in pg.event.get():
            if event.type == pg.QUIT:
    
                done = True
            config_window.update(event)
        config_window.draw(screen)
        pressed = pg.key.get_pressed()
        if pressed[pg.K_ESCAPE]:
            done = True
        pg.display.flip()
        clock.tick(60)

    pg.quit()