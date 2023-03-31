import pygame as pg
from config import Config as cfg

class UIElement():
    def __init__(self, position,
                text_color= (255,255,255), 
                 bg_color=(37, 37, 38), 
                 bg_color_hover=(42, 45, 46),
                 bg_color_selected=(55, 55, 61)):
        
        self.position = position
        self.mouse_over = False # Mouse is over the element
        self.selected = False   # Element is selected (clicked)

        self._text_color = text_color          # The text color of the element
        self._bg_color = bg_color              # The background color of the element
        self._bg_color_hover = bg_color_hover  # The background color when the mouse is over the element
        self._bg_color_selected = bg_color_selected # The background color when the element is selected
        self._bg_color_active = self._bg_color # The current background color

    def update(self, event):
        ...

    def draw(self, screen):
        ...

class UIContainer(UIElement):
    def __init__(self, position, size):
        super().__init__(position)
        self.size = size
        self.elements = []

    def update(self, event):
        self.rect = pg.Rect(self.position, self.size)
        for element in self.elements:
            element.update(event)

    def add_element(self, element: UIElement):
        if hasattr(element, 'position'):
            element.position = (element.position[0] + self.position[0], element.position[1] + self.position[1])
        if hasattr(element, 'start'):
            element.start = (element.start[0] + self.position[0], element.start[1] + self.position[1])
        if hasattr(element, 'end'):
            element.end = (element.end[0] + self.position[0], element.end[1] + self.position[1])
        self.elements.append(element)

    def clear_elements(self):
        self.elements = []

    def draw(self, screen):
        # create a surface from the rect
        self.image = pg.Surface(self.rect.size)
        # fill the surface with the color
        self.image.fill(self._bg_color)
        # draw the surface on the screen
        screen.blit(self.image, self.rect)

        for element in self.elements:
            element.draw(screen)

    def move_to(self, x, y):
        self._move(x - self.position[0], y - self.position[1])

    def _move(self, x, y):
        self.position = (self.position[0] + x, self.position[1] + y)
        for element in self.elements:
            if hasattr(element, 'position'):
                element.position = (element.position[0] + x, element.position[1] + y)
            if hasattr(element, 'start'):
                element.start = (element.start[0] + x, element.start[1] + y)
            if hasattr(element, 'end'):
                element.end = (element.end[0] + x, element.end[1] + y)


class UILine(UIElement):
    def __init__(self, start, end, color=(255,255,255), width=1):
        super().__init__(start)
        self.start = start
        self.end = end
        self.color = color
        self.width = width
    
    def draw(self, screen):
        pg.draw.line(screen, self.color, self.start, self.end, self.width)

class UIButton(UIElement):
    def __init__(self, position, size, text, action=None, args=None,
                 font_size= 16,
                 selected=False):
        super().__init__(position)
        self._action = action
        self._set_args(args)
        self._text = text
        self.size = size
        self._font = pg.font.SysFont("Helvetica ", font_size)
        self.center_position = (position[0] + size[0] // 2, position[1] + size[1] // 2)
        self.selected = selected

    def _set_args(self, args):
        if args is None:
            args = []
        if not isinstance(args, list):
            args = [args]
        self._args = args

    def update(self, event):
        self.rect = pg.Rect(self.position, self.size)
        
        # Handle hover events
        if event.type == pg.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self._bg_color_active = self._bg_color_hover
            else:
                self._bg_color_active = self._bg_color

        if self.selected:
            self._bg_color_active = self._bg_color_selected

        self.text_img = self._font.render(self._text, True, self._text_color, self._bg_color_active)
        
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
        self.image.blit(self.text_img, 
                        (self.rect.width // 2 - self.text_img.get_width() // 2, 
                        self.rect.height // 2 - self.text_img.get_height() // 2))
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



import time
class UIConfigElement(UIElement):
    '''
    A UI element that displays a value from a json file and allows to change it
    '''
    def __init__(self, position, size, 
                 json_key:str, 
                 font_size: int= 16):
        
        super().__init__(position)
        self._json_key = json_key
        self._json_value = cfg.get(json_key)
        self.size = size
        self._font = pg.font.SysFont("Helvetica ", font_size)
        self._bg_color_active = self._bg_color 
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
        self.text_img_key = self._font.render(varaiable_name, True, self._text_color, self._bg_color)
        position_key = (self.position[0], self.position[1])
        size_key = (self.size[0] * split_percent, self.size[1])
        self.rect_key = pg.Rect(position_key, size_key)
 
        # Right side of the UI element (value)
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
                    cfg.set(self._json_key, self.text_buffer)
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
                    cfg.set(self._json_key, self.text_buffer)
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
        # Draw Left side of the UI element (variable name)
        self.image1 = pg.Surface(self.rect_value.size)
        self.image1.fill(self._bg_color_active)
        self.image1.blit(self.text_img_value,
                        (self.rect_value.width // 2 - self.text_img_value.get_width() // 2,
                        self.rect_value.height // 2 - self.text_img_value.get_height() // 2))
        screen.blit(self.image1, self.rect_value)
        # Draw Right side of the UI element (variable value)
        self.image2 = pg.Surface(self.rect_key.size)
        self.image2.fill(self._bg_color)
        self.image2.blit(self.text_img_key, 
                        (self.rect_key.width // 2 - self.text_img_key.get_width() // 2,
                        self.rect_key.height // 2 - self.text_img_key.get_height() // 2))
        screen.blit(self.image2, self.rect_key)

        
class ConfigWindow(UIContainer):
    def __init__(self, position, size=(300,600)):
        super().__init__(position, size)

        self.spacing_top_tab_name = 10
        groups_in_config = cfg.get_groups()

        self.spacing_sides = 10
        self.spacing_between = 10
        self.elements_height = 25
        self.elements_width = self.size[0] - 2 * self.spacing_sides
        self.spacing_top = 40 + len(groups_in_config) * self.elements_height

        self.active_tab = groups_in_config[0]
        self.active_tab_old = self.active_tab
        self.create_tab()


    def create_tab(self):
        # Create config for active tab
        groups_in_config = cfg.get_groups()
        keys_in_config = cfg.get_keys(self.active_tab)
        elements = [UIConfigElement((0, 0), (0, 0), key) for key in keys_in_config]
        self.spacing_between = 5
        for i, element in enumerate(elements):
            element.position = (self.spacing_sides,self.spacing_top +  i * (self.elements_height + self.spacing_between))
            element.size = (self.elements_width, self.elements_height)
            self.add_element(element)

        # Create tab buttons
        index_active_tab = groups_in_config.index(self.active_tab)
        tab_names = [UIButton((0, 0), (0, 0), group.replace("_", " "), 
                              action=self.handle_tab_change, 
                              args=group,
                              font_size=18
                              ) for group in groups_in_config]
        for i, tab in enumerate(tab_names):
            tab.position = (self.spacing_sides, self.spacing_top_tab_name + i * (self.elements_height + self.spacing_between))
            tab.size = (self.elements_width, self.elements_height)
            if i == index_active_tab:
                tab.selected = True
            self.add_element(tab)

        # Add line between tab buttons and config elements
        line_y = 8 +  len(groups_in_config) * (self.elements_height+self.spacing_between)
        line = UILine((0, line_y), (self.elements_width, line_y), color=(100,100,100))
        self.add_element(line)

    def handle_tab_change(self, tab_name):
        self.active_tab = tab_name
        self.clear_elements()
        self.create_tab()
        self.update(pg.event.Event(pg.USEREVENT))


    def update(self, event):
        super().update(event)
    
    


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