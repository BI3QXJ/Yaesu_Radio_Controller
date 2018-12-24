 #!/usr/bin/env python
# -*- coding: utf-8 -*-
import yaml
import pygame
from pygame.locals import *


# 点击按钮类, BUTTON_UP触发
class Button(object):
    def __init__(self, surface, up_image, down_image, btnRect, btnFunc):
        self.button_up_image = pygame.image.load(up_image).convert_alpha()
        self.button_down_image = pygame.image.load(down_image).convert_alpha()
        self.button_rect = btnRect
        self.screen = surface
        self.pressed = False
        self.func = btnFunc
    
    def test_pressed(self, mouse_x, mouse_y, event):
        if self.button_rect.collidepoint(mouse_x, mouse_y) and event == MOUSEBUTTONDOWN:
            self.pressed = True
        elif self.button_rect.collidepoint(mouse_x, mouse_y) and event == MOUSEBUTTONUP and self.pressed:
            print 'Button Clicked: %s' % self.func
            self.pressed = False
        else:
            self.pressed = False
                
    def render(self):
        """ 依据按下状态进行绘制 """
        if self.pressed:
            self.screen.blit(self.button_down_image,(self.button_rect[0],self.button_rect[1]))
        else:
            self.screen.blit(self.button_up_image,(self.button_rect[0],self.button_rect[1]))

pygame.init()
pygame.mouse.set_visible(True)
screen = pygame.display.set_mode((300,200), 0, 32)

# def get_button_by_pos(btn_list, x, y):
#     for btn in btn_list:
#         if btn.button_rect.collidepoint(mouse_x, mouse_y):
#             return btn

def main():
    with open('button_config.yaml','r') as f:
        btn_config = yaml.load(f)
    global screen
    # active_panel = 'PANEL_1'
    # buttons = {}
    # for panel, button_list in btn_config['GROUP'].iteritems():
    #     buttons[panel] = []
    #     for btn in button_list:
    #         buttons[panel].append(
    #             Button(
    #                 screen
    #                 ,btn_config['BUTTONS'][btn]['UP']
    #                 ,btn_config['BUTTONS'][btn]['DOWN']
    #                 ,btn_config['BUTTONS'][btn]['RECT']
    #                 ,True if btn_config['BUTTONS'][btn]['TYPE'] == 'SWITCH' else False
    #                 )
    #             )
    # x, y = 0, 0
    # print get_button_by_pos(buttons[active_panel], x, y)


    FPS = 30
    fpsClock = pygame.time.Clock()
    btn_1 = Button(screen, 'button_up.png', 'button_down.png', Rect(100,100,70,46), 'Button1')
    btn_2 = Button(screen, 'button_up.png', 'button_down.png', Rect(200,100,70,46), 'Button2')
    
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
