 #!/usr/bin/env python
# -*- coding: utf-8 -*-
import yaml
import pygame
from pygame.locals import *

class Button(object):
    def __init__(self, surface, up_image, down_image, btnRect, btnFunc, funcDict):
        self.button_up_image = pygame.image.load(up_image).convert_alpha()
        self.button_down_image = pygame.image.load(down_image).convert_alpha()
        self.button_rect = btnRect
        self.surface = surface
        self.pressed = False
        self.func = btnFunc
        self.funcs = funcDict
    
    def test_pressed(self, mouse_x, mouse_y, event):
        if self.button_rect.collidepoint(mouse_x, mouse_y) and event == MOUSEBUTTONDOWN:
            self.pressed = True
        elif self.button_rect.collidepoint(mouse_x, mouse_y) and event == MOUSEBUTTONUP and self.pressed:
            # print 'Button Clicked: %s' % self.func
            self.funcs[self.func]()
            self.pressed = False
        else:
            self.pressed = False
                
    def render(self):
        """ 依据按下状态进行绘制 """
        if self.pressed:
            self.surface.blit(self.button_down_image,(self.button_rect[0],self.button_rect[1]))
        else:
            self.surface.blit(self.button_up_image,(self.button_rect[0],self.button_rect[1]))

def func1():
    print 'func1'

def func2():
    print 'func2'

def main():
    func_dict = {
        'func1': func1
        ,'func2': func2
    }
    pygame.init()
    pygame.mouse.set_visible(True)
    screen = pygame.display.set_mode((300,200), 0, 32)

    with open('button_config.yaml','r') as f:
        btn_config = yaml.load(f)
    # global screen

    FPS = 30
    fpsClock = pygame.time.Clock()
    btn_1 = Button(screen, 'button_up.png', 'button_down.png', Rect(100,100,70,46), 'func1', func_dict)
    btn_2 = Button(screen, 'button_up.png', 'button_down.png', Rect(200,100,70,46), 'func2', func_dict)
    
    while True:
        mouse_clicked = False
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame.quit()
                exit()
            elif event.type == MOUSEBUTTONDOWN or event.type == MOUSEBUTTONUP:
                x, y = pygame.mouse.get_pos()
                btn_1.test_pressed(x, y, event.type)
                btn_2.test_pressed(x, y, event.type)

        screen.fill((0,255,0))
        btn_1.render()
        btn_2.render()
        pygame.display.update()
        fpsClock.tick(FPS)
        
if __name__ == '__main__':
    main()
