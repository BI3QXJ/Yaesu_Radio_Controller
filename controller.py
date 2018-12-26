#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
线程[Remote_Controller]: 负责依据当前各状态, 进行绘制显示
    - 设备状态
    - 界面PANEL选择状态
        - 打开PANEL时刷新全部开关状态
    - 接受用户输入, 完成交互
线程[Rig_Polling]: 负责与设备通信, 持续获取设备状态
    - 获取频率值
        - VFO-A 以最多时间片获取, 保证刷新及时, VFO-B以第三优先级获取
        - 经过一段实践频率不发生变更时, 降低优先级, 减少获取次数, 发生变更时提高频率
    - 系统状态以第二优先级获取, 保证每秒2次以上获取
    - 接收时只获取S表, 发射时只获取PO/SWR/+CUSTOM
    - 不显示的功能参数不自动刷新, 仅当设置时刷新显示
    - 各状态标签轮转扫描, 分散压力
线程1\2通信:
    - 1从2获取状态, 分为手动刷新和自动刷新
    - 1向2发送命令, 进入2的执行队列
        - 手动刷新指令, 要求获取部分未显示的参数, 刷新完成后在公共变量中获取
        - SET命令 

'''

import pytz
import random
import datetime
import time
import yaml
import pygame
from pygame.locals import *
from sys import exit
import threading
import Queue
import rig

# global vars
VGA_SCREEN  = (640,480)
HVGA_SCREEN = (480,320)

IS_UTC = False

af_gain  = 0
rf_gain  = 0
mic_gain = 0
vox_gain = 0
rf_power = 0
nb_val   = 0
nr_val   = 0
mon_val  = 0

channel_no = 0

vfo_a_freq = '014270000'
vfo_b_freq = '007055000'
vfo_a_mode = 'USB'
vfo_b_mode = 'USB'
vfo_a_clar_status = 'OFF'
vfo_b_clar_status = 'OFF'
vfo_a_clar_offset = '0000'
vfo_b_clar_offset = '0000'
vfo_a_clar_direct = '+'
vfo_b_clar_direct = '+'

agc_status  = 'OFF'
att_status  = 'OFF'
bkin_status = 'OFF'
cnt_status  = 'OFF'
dnf_status  = 'OFF'
ipo_status  = 'OFF'
meq_status  = 'OFF'
mon_status  = 'OFF'
nar_status  = 'OFF'
nch_status  = 'OFF'
nb_status   = 'OFF'
nr_status   = 'OFF'
prc_status  = 'OFF'
sft_status  = 'OFF'
spl_status  = 'OFF'
tnr_status  = 'OFF'
vox_status  = 'OFF'

rx_led      = 'OFF'
tx_led      = 'OFF'
hi_swr_led  = 'OFF'
play_led    = 'OFF'
rec_led     = 'OFF'

meter_s_val = 70
meter_swr_val = 0
meter_po_val = 0
meter_custom = 'CMP'
meter_custom_val = 0

job_queue = Queue.Queue()

class Rig_Polling(threading.Thread):
    def __init__(self, radio_moel):
        super(Rig_Polling, self).__init__()
        creator = rig.RIG()
        self.rig = creator.connect(radio_moel)
        
    def run(self):
        global vfo_a_freq, vfo_b_freq, vfo_a_mode, vfo_b_mode
        global vfo_a_clar_status, vfo_b_clar_status, vfo_a_clar_offset, vfo_b_clar_offset, vfo_a_clar_direct, vfo_b_clar_direct
        global agc_status, att_status, bkin_status, cnt_status, dnf_status, ipo_status, meq_status, mon_status, nar_status, nch_status, nb_status, nr_status, prc_status, sft_status, spl_status, tnr_status, vox_status
        global af_gain, rf_gain, mic_gain, vox_gain, rf_power, nb_val, nr_val, mon_val
        global rx_led, tx_led, hi_swr_led, play_led, rec_led
        global meter_s_val, meter_swr_val, meter_po_val, meter_custom, meter_custom_val

        # VFO/TAG/GAIN poll frequency (query every n times)
        QUERY_VFO_HI = 2
        QUERY_VFO_LO = 10
        QUERY_TAG_HI= 10
        QUERY_TAG_LO = 50
        QUERY_GAIN_HI = 10
        QUERY_GAIN_LO = 30
        QUERY_METER_HI = 3
        QUERY_METER_LO = 10

        count = 0
        poll_freq_vfo = QUERY_VFO_HI
        poll_freq_tag = QUERY_TAG_HI
        poll_freq_gain = QUERY_GAIN_HI
        poll_freq_meter = QUERY_METER_HI

        timer = time.time()
        timer_vfo_hi = time.time()
        vfo_a_last = '000000000'

        while True:      
            # thread job operation
            try:
                recv_job = job_queue.get_nowait()
            except Queue.Empty:
                pass
            else:
                pass

            # vfo get
            if count % poll_freq_vfo == 0:
                vfo_a_info = self.rig.vfo_info('A')
                vfo_b_info = self.rig.vfo_info('B')

                vfo_a_freq = vfo_a_info['FREQ']
                vfo_a_mode = vfo_a_info['MODE']
                vfo_a_clar_status = vfo_a_info['CLAR_STATUS']   # OFF/ON
                vfo_a_clar_direct = vfo_a_info['CLAR_DIRECT']   # +/-
                vfo_a_clar_offset = vfo_a_info['CLAR_OFFSET']   # 0000
                vfo_b_freq = vfo_b_info['FREQ']
                vfo_b_mode = vfo_b_info['MODE']
                vfo_b_clar_status = vfo_b_info['CLAR_STATUS']
                vfo_b_clar_direct = vfo_b_info['CLAR_DIRECT']
                vfo_b_clar_offset = vfo_b_info['CLAR_OFFSET']

                if poll_freq_vfo == QUERY_VFO_LO:
                    if vfo_a_freq <> vfo_a_last:
                        poll_freq_vfo = QUERY_VFO_HI
                        timer_vfo_hi = time.time()
                        vfo_a_last = vfo_a_freq
                elif poll_freq_vfo == QUERY_VFO_HI:
                    if vfo_a_freq <> vfo_a_last:
                        timer_vfo_hi = time.time()
                        vfo_a_last = vfo_a_freq
                    elif time.time() - timer_vfo_hi > 5.0:
                        poll_freq_vfo = QUERY_VFO_LO

            # balance gain val query by two parts
            if count % poll_freq_gain == 2:
                af_gain = self.rig.af_gain_get()['VAL']
                rf_gain = self.rig.rf_gain_get()['VAL']

            if count % poll_freq_gain == 8:
                mic_gain = self.rig.mic_gain_get()['VAL']
                vox_gain = self.rig.vox_gain_get()['VAL']
                rf_power = self.rig.rf_power_get()['VAL']
            
            if count % poll_freq_tag == 0:
                agc_status  = self.rig.agc_get()['MODE']
                att_status  = self.rig.att_get()['STATUS']
                bkin_status = self.rig.bkin_get()['STATUS']
                cnt_status  = self.rig.contour_get()['STATUS']
                # dnf_status  = self.rig.agc_get()['STATUS']
                ipo_status  = self.rig.ipo_get()['STATUS']
                # meq_status  = self.rig.agc_get()['STATUS']
                mon_status  = self.rig.monitor_get()['STATUS']
                nar_status  = self.rig.narrow_get()['STATUS']
                # nch_status  = self.rig.nch_get()['STATUS']
                # nb_status   = self.rig.nb_get()['STATUS']
                # nr_status   = self.rig.nr_get()['STATUS']
                prc_status  = self.rig.prc_get()['STATUS']
                # sft_status  = self.rig.shift_get()['STATUS']
                # spl_status  = self.rig.split_get()['STATUS']
                tnr_status  = self.rig.atu_get()['STATUS']
                vox_status  = self.rig.vox_get()['STATUS']

            if count % poll_freq_meter == 0:
                meter_s_val = self.rig.meter('S')['VAL']
                meter_swr_val = self.rig.meter('SWR')['VAL']
                meter_po_val = self.rig.meter('PO')['VAL']

            # time.sleep(0.01)
            count = count + 1

            if count > 2000:
                count = 0
                # print '2000s CAT Oper cost: %d' % int(time.time() - timer)
                timer = time.time()

    def get_rxtx(self):
        # RI or GET Po Meter
        self.__rig.get_rxtx()
    
    def get_freq_a(self):
        pass

class Button(object):
    def __init__(self, surface, up_image, down_image, button_Rect):
        self.button_up_image = pygame.image.load(up_image).convert_alpha()
        self.button_down_image = pygame.image.load(down_image).convert_alpha()
        self.button_rect = button_Rect
        self.pressed = False
        self.screen = surface
    
    def test_pressed(self, mouse_x, mouse_y, press=True):
        if self.button_rect.collidepoint(mouse_x, mouse_y) and press:
            print 'Clicked.'
            self.pressed = True
        else:
            print 'Not Clicked.'
            self.pressed = False

    def render(self):
        if self.pressed:
            self.screen.blit(self.button_down_image,(100,100))
        else:
            self.screen.blit(self.button_up_image,(100,100))

class Remote_Controller(object):
    def __init__(self, model, resolution='VGA', display_mode=0):  # FULLSCREEN
        '''
        model: radio model
        resolution: HVGA/VGA/HD
        display_mode:0=windows,FULLSCREEN
        '''
        self.model = model

        with open('conf/layout.yaml','r') as f:
             ui_conf = yaml.load(f)[resolution]
        print ui_conf['RESOLUTION']
        self.__layout = ui_conf
        
        self.screen = pygame.display.set_mode(eval(ui_conf['RESOLUTION']), display_mode, 32)
        pygame.display.set_caption(model)
        
        self.background = pygame.image.load(ui_conf['BACKGROUND']).convert()
        # 全部元素图像+位置
        self.elements = {}
        # 图标类显示元素
        self.icons = {
            'MODEL': 'FT-891'
            ,'AGC': 'FAST'
            ,'ATT': 'ON'
            ,'BK-IN': 'ON'
            ,'CNT': 'ON'
            ,'DNF': 'ON'
            ,'IPO': 'ON'
            ,'MEQ': 'ON'
            ,'MON': 'ON'
            ,'NAR': 'ON'
            ,'NCH': 'OFF'
            ,'NB': 'ON'
            ,'NR': 'OFF'
            ,'PRC': 'OFF'
            ,'SFT': 'OFF'
            ,'SPL': 'OFF'
            ,'TNR': 'OFF'
            ,'VOX': 'OFF'
            ,'WDH': 'OFF'
            # ,'SQL': 'OFF'     # NOT READY

            # VFO A/B
            ,'VFO_A_MODE': 'USB'
            ,'VFO_B_MODE': 'CW-U'
            ,'VFO_A_CLAR': 'RX'
            ,'VFO_A_CLAR_DIRECTION': '+'
            ,'VFO_B_CLAR': 'OFF'
            ,'VFO_B_CLAR_DIRECTION': '+'
            
            # LED
            ,'RX': 'OFF'
            ,'TX': 'OFF'
            # ,'HI-SWR': 'OFF'  # NOT READY
            # ,'REC': 'OFF'     # NOT READY
            # ,'PLAY': 'OFF'    # NOT READY

            ,'PANEL': 'BAND'
        }
        
        # 数值类显示元素
        self.values = {
            # RF POWER
            'RF_POWER_1': '0'
            ,'RF_POWER_2': '0'
            ,'RF_POWER_3': '0'
            # GAIN
            ,'RF_GAIN_1': '0'
            ,'RF_GAIN_2': '0'
            ,'RF_GAIN_3': '0'
            ,'AF_GAIN_1': '0'
            ,'AF_GAIN_2': '0'
            ,'AF_GAIN_3': '0'
            ,'MIC_GAIN_1': '0'
            ,'MIC_GAIN_2': '0'
            ,'MIC_GAIN_3': '0'
            ,'VOX_GAIN_1': '0'
            ,'VOX_GAIN_2': '0'
            ,'VOX_GAIN_3': '0'

            # DATETIME
            ,'DATE_1': '2'
            ,'DATE_2': '0'
            ,'DATE_3': '1'
            ,'DATE_4': '8'
            ,'DATE_5': '1'
            ,'DATE_6': '2'
            ,'DATE_7': '1'
            ,'DATE_8': '1'
            ,'TIME_1': '2'
            ,'TIME_2': '3'
            ,'TIME_3': '0'
            ,'TIME_4': '9'
            ,'TIME_5': '0'
            ,'TIME_6': '1'

            # VFO_A/B
            ,'VFO_A_FREQ_1': '0'
            ,'VFO_A_FREQ_2': '0'
            ,'VFO_A_FREQ_3': '0'
            ,'VFO_A_FREQ_4': '0'
            ,'VFO_A_FREQ_5': '0'
            ,'VFO_A_FREQ_6': '0'
            ,'VFO_A_FREQ_7': '0'
            ,'VFO_A_FREQ_8': '0'
            ,'VFO_A_FREQ_9': '0'
            ,'VFO_B_FREQ_1': '0'
            ,'VFO_B_FREQ_2': '0'
            ,'VFO_B_FREQ_3': '0'
            ,'VFO_B_FREQ_4': '0'
            ,'VFO_B_FREQ_5': '0'
            ,'VFO_B_FREQ_6': '0'
            ,'VFO_B_FREQ_7': '0'
            ,'VFO_B_FREQ_8': '0'
            ,'VFO_B_FREQ_9': '0'
            ,'VFO_A_CLAR_OFFSET_1': '0'
            ,'VFO_A_CLAR_OFFSET_2': '0'
            ,'VFO_A_CLAR_OFFSET_3': '0'
            ,'VFO_A_CLAR_OFFSET_4': '0'
            ,'VFO_B_CLAR_OFFSET_1': '0'
            ,'VFO_B_CLAR_OFFSET_2': '0'
            ,'VFO_B_CLAR_OFFSET_3': '0'
            ,'VFO_B_CLAR_OFFSET_4': '0'
            ,'NB_VAL_1': '0'
            ,'NB_VAL_2': '1'
            ,'NR_VAL_1': ' '
            ,'NR_VAL_2': ' '
            ,'MON_VAL_1': ' '
            ,'MON_VAL_2': ' '
        }

        self.meter_values = {
            'METER_1': 100
            ,'METER_2': 250
            ,'METER_3': 30
            ,'METER_4': 200
        }
        self.meter_select = {
            'METER_1': 'S'
            ,'METER_2': 'SWR'
            ,'METER_3': 'PO'
            ,'METER_4': 'CMP'
        }

        # 当前生效按钮
        self.buttons = {}
        for i in range(1,10):
            for v in ('A','B'):
                pos = eval(self.__layout['ELEMENTS']['VFO_'+ v +'_FREQ_' + str(i)]['POS'])
                size = eval(self.__layout['ELEMENTS']['VFO_'+ v +'_FREQ_' + str(i)]['SIZE'])
                self.buttons['BUTTON_VFO_'+ v +'_' + str(i)] = (pos, size)

    def init_resouce(self):
        for k, v in self.__layout['ELEMENTS'].iteritems():
            # print k
            self.elements[k] = {
                'POS': eval(v['POS'])
                ,'RES': self.load_resouce(v['PATH'], eval(v['SIZE']), v['STAT'])
                }

    def load_resouce(self, path, size, stat_list, vertical=True):
        pic = pygame.image.load(path).convert_alpha()
        stat_with_res = {}
        start_pos = [0, 0]
        for i in range(len(stat_list)):
            if vertical:
                stat_with_res[stat_list[i]] = pic.subsurface(start_pos, size)
                start_pos = [0, start_pos[1] + size[1]]
            else:
                stat_with_res[stat_list[i]] = pic.subsurface(start_pos, size)
                start_pos = [start_pos[1] + size[1], 0]
        return stat_with_res

    def draw_icons(self):
        for k, v in self.icons.iteritems():
            # print k,v
            self.screen.blit(self.elements[k]['RES'][v], self.elements[k]['POS'])
    
    def draw_values(self):
        for k, v in self.values.iteritems():
            # print k,v
            self.screen.blit(self.elements[k]['RES'][v], self.elements[k]['POS'])
    
    def draw_meters(self):
        # draw meter background
        for k, v in self.meter_select.iteritems():
            self.screen.blit(self.elements[k]['RES'][v], self.elements[k]['POS'])
        # draw meter bar
        for k, v in self.meter_values.iteritems():
            pygame.draw.rect(
                self.screen
                ,eval(self.__layout['ELEMENTS'][k]['COLOR'])
                ,(
                    eval(self.__layout['ELEMENTS'][k]['BAR'])
                    ,(int(v * self.__layout['ELEMENTS'][k]['RATIO']), self.__layout['ELEMENTS'][k]['BAR_WIDTH'])
                )
            )

    def clock(self,timezone='Asia/Shanghai'):
        global IS_UTC
        tz = pytz.timezone('UTC') if IS_UTC else pytz.timezone(timezone)
        dt = datetime.datetime.now(tz).strftime('%Y%m%d-%H%M%S').split('-')
        for i in range(1,9):
            self.values['DATE_' + str(i)] = dt[0][i-1]
        for i in range(1,7):
            self.values['TIME_' + str(i)] = dt[1][i-1]

    def sync(self):
        '''
        synchronize rig's status from rig_polling
        '''
        global vfo_a_freq, vfo_b_freq, vfo_a_mode, vfo_b_mode
        global vfo_a_clar_status, vfo_b_clar_status, vfo_a_clar_offset, vfo_b_clar_offset, vfo_a_clar_direct, vfo_b_clar_direct
        global agc_status, att_status, bkin_status, cnt_status, dnf_status, ipo_status, meq_status, mon_status, nar_status, nch_status, nb_status, nr_status, prc_status, sft_status, spl_status, tnr_status, vox_status
        global af_gain, rf_gain, mic_gain, vox_gain, rf_power, nb_val, nr_val, mon_val
        global rx_led, tx_led, hi_swr_led, play_led, rec_led
        global meter_s_val, meter_swr_val, meter_po_val, meter_custom, meter_custom_val

        # set meter val
        self.meter_values['METER_1'] = meter_s_val
        self.meter_values['METER_2'] = meter_swr_val
        self.meter_values['METER_3'] = meter_po_val

        self.meter_select['METER_4'] = meter_custom
        self.meter_values['METER_4'] = meter_custom_val

        # set rf_power
        rf_power_display = str(rf_power).rjust(3,' ')
        for i in range(1,4):
            self.values['RF_POWER_'+str(i)] = rf_power_display[i-1]

        # set vfo
        self.icons['VFO_A_MODE'] = vfo_a_mode
        self.icons['VFO_B_MODE'] = vfo_b_mode
        vfo_a_freq_display = vfo_a_freq.lstrip('0').rjust(9,' ')
        vfo_b_freq_display = vfo_b_freq.lstrip('0').rjust(9,' ')
        for i in range(1,10):
            self.values['VFO_A_FREQ_' + str(i)] = vfo_a_freq_display[i-1]
            self.values['VFO_B_FREQ_' + str(i)] = vfo_b_freq_display[i-1]

        # set CLAR
        self.icons['VFO_A_CLAR'] = vfo_a_clar_status
        self.icons['VFO_B_CLAR'] = vfo_b_clar_status
        self.values['VFO_A_CLAR_DIRECTION'] = vfo_a_clar_direct
        self.values['VFO_B_CLAR_DIRECTION'] = vfo_b_clar_direct
        for i in range(1,5):
            self.values['VFO_A_CLAR_OFFSET_' + str(i)] = vfo_a_clar_offset[i-1]
            self.values['VFO_B_CLAR_OFFSET_' + str(i)] = vfo_b_clar_offset[i-1]


        # set GAIN and RF_POWER
        rf_gain_display = str(rf_gain).rjust(3,' ')
        af_gain_display = str(af_gain).rjust(3,' ')
        mic_gain_display = str(mic_gain).rjust(3,' ')
        vox_gain_display = str(vox_gain).rjust(3,' ')
        rf_power_display = str(rf_power).rjust(3,' ')
        for i in range(1,4):
            self.values['RF_GAIN_' + str(i)] = rf_gain_display[i-1]
            self.values['AF_GAIN_' + str(i)] = af_gain_display[i-1]
            self.values['MIC_GAIN_' + str(i)] = mic_gain_display[i-1]
            self.values['VOX_GAIN_' + str(i)] = vox_gain_display[i-1]
            self.values['RF_POWER_' + str(i)] = rf_power_display[i-1]
        
        # set function indicators
        self.icons['AGC']   = agc_status
        self.icons['ATT']   = att_status
        self.icons['BK-IN'] = bkin_status
        self.icons['CNT']   = cnt_status
        self.icons['DNF']   = dnf_status
        self.icons['IPO']   = ipo_status
        self.icons['MEQ']   = meq_status
        self.icons['MON']   = mon_status
        self.icons['NAR']   = nar_status
        self.icons['NCH']   = nch_status
        self.icons['NB']    = nb_status
        self.icons['NR']    = nr_status
        self.icons['PRC']   = prc_status
        self.icons['SFT']   = sft_status
        self.icons['SPL']   = spl_status
        self.icons['TNR']   = tnr_status
        self.icons['VOX']   = vox_status

    def render(self):
        self.sync()
        self.clock()
        self.screen.blit(self.background, (0,0))
        self.draw_icons()
        self.draw_values()
        self.draw_meters()
        pygame.display.update()

    def get_button(self, x, y):
        pass

def main():
    pygame.init()
    pygame.mouse.set_visible(False)

    # match maximum resolution
    all_support_display_modes = pygame.display.list_modes()
    if VGA_SCREEN in all_support_display_modes:
        screen_resolution = 'VGA'
    elif HVGA_SCREEN in all_support_display_modes:
        screen_resolution = 'HVGA'
    else:
        print 'NOT SUPPORT SCREEN RESOLUTION.(Only VGA or HVGA supported)'
        exit()

    # for debug
    # screen_resolution = 'HVGA'
    dp_mode = FULLSCREEN

    with open('conf/custom.yaml','r') as f:
        custome_config = yaml.load(f)
    model = custome_config['RADIO']['MODEL']
    port = custome_config['RADIO']['PORT']
    baudrate = custome_config['RADIO']['BAUDRATE']

    FPS = 30
    fpsClock = pygame.time.Clock()
    rc = Remote_Controller(model=model, resolution=screen_resolution, display_mode=dp_mode)
    rc.init_resouce()
    poll = Rig_Polling(model)
    poll.setDaemon(True)
    poll.start()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                exit()
        rc.render()
        fpsClock.tick(FPS)
        

if __name__ == '__main__':
    main()
