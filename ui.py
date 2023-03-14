import pygame as pg


class UIElement():
    def __init__(self, position):
        self.position = position
        self.mouse_over = False

    def update(self, event):
        ...

    def draw(self, screen):
        ...

class UIButton(UIElement):
    def __init__(self, position, size, text, action=None, font_size= 16, text_color= (255,255,255), bg_color=(0,0,0), bg_color_hover=(50,50,50)):
        super().__init__(position)
        self._action = action
        self._text = text
        self.size = size
        self._font = pg.font.SysFont("Helvetica ", font_size)
        self._bg_color = bg_color
        self._bg_color_hover = bg_color_hover
        self._bg_color_active = self._bg_color
        self._text_color = text_color
        self.center_position = (position[0] + size[0] // 2, position[1] + size[1] // 2)

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
                    self._action()

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