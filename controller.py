#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytz
import random
import datetime
import time
import yaml
import Queue
import threading
import pygame
from pygame.locals import *
from sys import exit
import rig

# global vars
IS_UTC = False

af_gain  = 0
rf_gain  = 0
mic_gain = 0
vox_gain = 0
rf_power = 0
nb_val   = 10
nr_val   = 11
mon_val  = 20

channel_no = 0
vfo_a_freq = '014270000'
vfo_b_freq = '007055000'
vfo_a_mode = 'USB'
vfo_b_mode = 'USB'
vfo_a_clar_status = 'ON'
vfo_b_clar_status = 'OFF'
vfo_a_clar_offset = '0300'
vfo_b_clar_offset = '0000'
vfo_a_clar_direct = '+'
vfo_b_clar_direct = '+'

agc_status  = 'OFF'
att_status  = 'ON'
bkin_status = 'ON'
cnt_status  = 'ON'
dnf_status  = 'ON'
ipo_status  = 'ON'
meq_status  = 'ON'
mon_status  = 'ON'
nar_status  = 'ON'
nch_status  = 'AUTO'
nb_status   = 'ON'
nr_status   = 'ON'
prc_status  = 'ON'
sft_status  = 'ON'
spl_status  = 'ON'
tnr_status  = 'ON'
vox_status  = 'ON'

rx_led      = 'OFF'
tx_led      = 'OFF'
hi_swr_led  = 'OFF'
play_led    = 'OFF'
rec_led     = 'OFF'

meter_s_val = 100
meter_swr_val = 100
meter_po_val = 100
meter_custom = 'CMP'
meter_custom_val = 0

rig_job_queue = Queue.Queue()

class Rig_Polling(threading.Thread):
    """ Class for Rig Polling Thread """
    def __init__(self, radio_model):
        super(Rig_Polling, self).__init__()
        creator = rig.RIG()
        self.rig = creator.connect(radio_model)
        self.button_funcs = {
            'BUTTON_BAND_1_8': 'BS00;'
            ,'BUTTON_BAND_3_5': 'BS01;'
            ,'BUTTON_BAND_5_3': 'BS02;'
            ,'BUTTON_BAND_7': 'BS03;'
            ,'BUTTON_BAND_10': 'BS04;'
            ,'BUTTON_BAND_14': 'BS05;'
            ,'BUTTON_BAND_18': 'BS06;'
            ,'BUTTON_BAND_21': 'BS07;'
            ,'BUTTON_BAND_24': 'BS08;'
            ,'BUTTON_BAND_28': 'BS09;'
            ,'BUTTON_BAND_50': 'BS10;'
            ,'BUTTON_BAND_GEN': 'BS11;'
            ,'BUTTON_BAND_MW': 'BS12;'
            ,'BUTTON_BAND_AIR': 'BS14;'
            ,'BUTTON_BAND_144': 'BS15;'
            ,'BUTTON_BAND_430': 'BS16;'
        }
        
    def run(self):
        global vfo_a_freq, vfo_b_freq, vfo_a_mode, vfo_b_mode
        global vfo_a_clar_status, vfo_b_clar_status, vfo_a_clar_offset, vfo_b_clar_offset, vfo_a_clar_direct, vfo_b_clar_direct
        global agc_status, att_status, bkin_status, cnt_status, dnf_status, ipo_status, meq_status, mon_status, nar_status, nch_status, nb_status, nr_status, prc_status, sft_status, spl_status, tnr_status, vox_status
        global af_gain, rf_gain, mic_gain, vox_gain, rf_power, nb_val, nr_val, mon_val
        global rx_led, tx_led, hi_swr_led, play_led, rec_led
        global meter_s_val, meter_swr_val, meter_po_val, meter_custom, meter_custom_val

        # VFO/TAG/GAIN poll frequency (query every n times)
        QUERY_VFO_HI = 10
        QUERY_VFO_LO = 10
        QUERY_TAG_HI= 50
        QUERY_TAG_LO = 50
        QUERY_GAIN_HI = 10
        QUERY_GAIN_LO = 50
        QUERY_METER_HI = 10
        QUERY_METER_LO = 30

        count = 0
        poll_freq_vfo = 10
        poll_freq_meter = 10
        poll_freq_vfo = QUERY_VFO_HI
        poll_freq_tag = QUERY_TAG_HI
        poll_freq_gain = QUERY_GAIN_HI
        poll_freq_meter = QUERY_METER_HI

        # timer = time.time()
        # timer_vfo_hi = time.time()
        # vfo_a_last = '000000000'

        while True:      
            # thread job operation
            try:
                recv_job = rig_job_queue.get_nowait()
            except Queue.Empty:
                pass
            else:
                print recv_job
                self.rig.cmd_w(self.button_funcs[recv_job])
            
            # continue

            # vfo get
            # A,A,A,A,B,A+,A,A,A,B+
            vfo_query_switch = count % poll_freq_vfo
            if vfo_query_switch in (1,2,3,4,7,8,9):
                vfo_a_freq = self.rig.vfo_freq('A')['FREQ']
            elif vfo_query_switch in (6,):
                vfo_a_info = self.rig.vfo_info('A')
                vfo_a_freq = vfo_a_info['FREQ']
                vfo_a_mode = vfo_a_info['MODE']
                vfo_a_clar_status = vfo_a_info['CLAR_STATUS']   # OFF/ON
                vfo_a_clar_direct = vfo_a_info['CLAR_DIRECT']   # +/-
                vfo_a_clar_offset = vfo_a_info['CLAR_OFFSET']   # 0000
            elif vfo_query_switch in (5,):
                vfo_b_freq = self.rig.vfo_freq('B')['FREQ'] 
            elif vfo_query_switch in (0,):
                vfo_b_info = self.rig.vfo_info('B')
                vfo_b_freq = vfo_b_info['FREQ']
                vfo_b_mode = vfo_b_info['MODE']
                vfo_b_clar_status = vfo_b_info['CLAR_STATUS']
                vfo_b_clar_direct = vfo_b_info['CLAR_DIRECT']
                vfo_b_clar_offset = vfo_b_info['CLAR_OFFSET']
            
            # # vfo_a freq change
            #     if poll_freq_vfo == QUERY_VFO_LO:
            #         if vfo_a_freq <> vfo_a_last:
            #             poll_freq_vfo = QUERY_VFO_HI
            #             timer_vfo_hi = time.time()
            #             vfo_a_last = vfo_a_freq
            #     elif poll_freq_vfo == QUERY_VFO_HI:
            #         if vfo_a_freq <> vfo_a_last:
            #             timer_vfo_hi = time.time()
            #             vfo_a_last = vfo_a_freq
            #         elif time.time() - timer_vfo_hi > 5.0:
            #             poll_freq_vfo = QUERY_VFO_LO

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
            elif count % poll_freq_meter == 3:
                meter_swr_val = self.rig.meter('SWR')['VAL']
            elif count % poll_freq_meter == 6:
                meter_po_val = self.rig.meter('PO')['VAL']

            # time.sleep(0.01)
            count = count + 1

            if count > 100:
                count = 0
                # print '2000s CAT Oper cost: %d' % int(time.time() - timer)
                # timer = time.time()

    def get_rxtx(self):
        # RI or GET Po Meter
        self.__rig.get_rxtx()
    
    def get_freq_a(self):
        pass

class Button(object):
    """ Class for button, click to invoke function, trigger by MOUSEBUTTONUP """
    def __init__(self, surface, up_image, down_image, btnRect, btnFunc):
        self.button_up_image = pygame.image.load(up_image).convert_alpha()
        self.button_down_image = pygame.image.load(down_image).convert_alpha()
        self.button_rect = btnRect
        self.surface = surface
        self.pressed = False
        self.func = btnFunc
    
    def test_pressed(self, mouse_x, mouse_y, event):
        if self.button_rect.collidepoint(mouse_x, mouse_y) and event == MOUSEBUTTONDOWN:
            self.pressed = True
        elif self.button_rect.collidepoint(mouse_x, mouse_y) and event == MOUSEBUTTONUP and self.pressed:
            # self.funcs[self.func]()
            # print self.func
            global rig_job_queue
            rig_job_queue.put(self.func)
            self.pressed = False
        else:
            self.pressed = False
                
    def render(self):
        if self.pressed:
            self.surface.blit(self.button_down_image,(self.button_rect[0],self.button_rect[1]))
        else:
            self.surface.blit(self.button_up_image,(self.button_rect[0],self.button_rect[1]))

class Switch(object):
    """ Class for Switch, click to switch status, trigger by MOUSEBUTTONUP """
    def __init__(self, surface, stat_images, stat_list, btnRect):
        self.stats = stat_list
        self.current_stat = ''

    def test_pressed(self, mouse_x, mouse_y, event):
        pass
    def render(self):
        pass

class Remote_Controller(object):
    def __init__(self, model, resolution, display_mode=0):
        '''
        model: radio model
        resolution: HVGA/VGA/HD
        display_mode:0=windows, FULLSCREEN
        '''
        self.model = model

        with open('conf/layout.yaml','r') as f:
             ui_conf = yaml.load(f)[resolution]
        print resolution, ui_conf['RESOLUTION']
        self.__layout = ui_conf
        
        self.screen = pygame.display.set_mode(eval(ui_conf['RESOLUTION']), display_mode, 32)
        pygame.display.set_caption(model)
        
        self.background = pygame.image.load(ui_conf['BACKGROUND']).convert()
        # 全部元素图像+位置
        self.elements = {}
        # 当前生效按钮
        self.buttons = {}
        # self.active_panel = 'BAND'
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
            ,'TX': 'ON'

            ,'PANEL': 'BAND'
        }
        
        # 数值类显示元素
        self.values = {
            # RF POWER
            'RF_POWER_1': '0'
            ,'RF_POWER_2': '0'
            ,'RF_POWER_3': '0'
            ,'RF_GAIN_1': '0'       # GAIN
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
            ,'DATE_1': '2'          # DATETIME
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
            ,'VFO_A_FREQ_1': '0'    # VFO_A/B
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
            ,'NB_VAL_1': ' '
            ,'NB_VAL_2': ' '
            ,'NR_VAL_1': ' '
            ,'NR_VAL_2': ' '
            ,'MON_VAL_1': ' '
            ,'MON_VAL_2': ' '
        }

        self.meter_values = {
            'METER_1': 100
            ,'METER_2': 150
            ,'METER_3': 200
            ,'METER_4': 250
        }

        self.meter_select = {
            'METER_1': 'S'
            ,'METER_2': 'SWR'
            ,'METER_3': 'PO'
            ,'METER_4': 'CMP'
        }

        self.warn_box = {
            'HI-SWR': 'OFF'
            # ,'REC': 'OFF'     # NOT READY
            # ,'PLAY': 'OFF'    # NOT READY
        }

    def init_resouce(self):
        """ init resouce of screen element """
        for k, v in self.__layout['ELEMENTS'].iteritems():
            # print k, v
            self.elements[k] = {
                'POS': eval(v['POS'])
                ,'RES': self.load_resouce(v['PATH'], eval(v['SIZE']), v['STAT'])
                }

    def init_button(self):
        for k,v in self.__layout['BUTTON']['GROUP'].iteritems():
            self.buttons[k] = {}
            print k,v
            for btn in v:
                self.buttons[k][btn] = Button(
                    self.screen
                    ,self.__layout['BUTTON']['BUTTONS'][btn]['UP']
                    ,self.__layout['BUTTON']['BUTTONS'][btn]['DOWN']
                    ,pygame.Rect(eval(self.__layout['BUTTON']['BUTTONS'][btn]['RECT']))
                    ,btn
                )
                # self.buttons[k][btn] = {
                #     'UP': pygame.image.load(self.__layout['BUTTON']['BUTTONS'][btn]['UP']).convert_alpha()
                #     ,'DOWN': pygame.image.load(self.__layout['BUTTON']['BUTTONS'][btn]['DOWN']).convert_alpha()
                #     ,'RECT': pygame.Rect(eval(self.__layout['BUTTON']['BUTTONS'][btn]['RECT']))
                #     ,'FUNC': self.__layout['BUTTON']['BUTTONS'][btn]['FUNC']
                #     ,'TYPE': self.__layout['BUTTON']['BUTTONS'][btn]['TYPE']
                # }

    def load_resouce(self, path, size, stat_list, vertical=True):
        """ load one picture, save into specific status in one dict """
        # print path, stat_list
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
        """ draw all icons res """
        for k, v in self.icons.iteritems():
            self.screen.blit(self.elements[k]['RES'][v], self.elements[k]['POS'])
    
    def draw_values(self):
        """ draw all values res """
        for k, v in self.values.iteritems():
            self.screen.blit(self.elements[k]['RES'][v], self.elements[k]['POS'])

    def draw_meters(self):
        """ draw meters in config """
        # draw meter background
        for k, v in self.meter_select.iteritems():
            self.screen.blit(self.elements[k]['RES'][v], self.elements[k]['POS'])
        # draw meter bar
        for k, v in self.meter_values.iteritems():
            if v > 0:
                pygame.draw.rect(
                    self.screen
                    ,eval(self.__layout['ELEMENTS'][k]['COLOR'])
                    ,(
                        eval(self.__layout['ELEMENTS'][k]['BAR'])
                        ,(int(v * self.__layout['ELEMENTS'][k]['RATIO']), self.__layout['ELEMENTS'][k]['BAR_WIDTH'])
                    )
                )
    
    def draw_buttons(self):
        for btn in self.buttons[self.icons['PANEL']].values():
            btn.render()

    def test_buttons(self, x, y, event):
        for btn in self.buttons[self.icons['PANEL']].values():
            btn.test_pressed(x, y, event)

    def draw_warning(self):
        """ draw warning box """
        for k, v in self.warn_box.iteritems():
            self.screen.blit(self.elements[k]['RES'][v], self.elements[k]['POS'])

    def clock(self, timezone='Asia/Shanghai'):
        """ draw clock """
        global IS_UTC
        tz = pytz.timezone('UTC') if IS_UTC else pytz.timezone(timezone)
        dt = datetime.datetime.now(tz).strftime('%Y%m%d-%H%M%S').split('-')
        for i in range(1,9):
            self.values['DATE_' + str(i)] = dt[0][i-1]
        for i in range(1,7):
            self.values['TIME_' + str(i)] = dt[1][i-1]

    def sync(self):
        """ synchronize rig's status from rig_polling """
        global vfo_a_freq, vfo_b_freq, vfo_a_mode, vfo_b_mode
        global vfo_a_clar_status, vfo_b_clar_status, vfo_a_clar_offset, vfo_b_clar_offset, vfo_a_clar_direct, vfo_b_clar_direct
        global agc_status, att_status, bkin_status, cnt_status, dnf_status, ipo_status, meq_status, mon_status, nar_status, nch_status, nb_status, nr_status, prc_status, sft_status, spl_status, tnr_status, vox_status
        global af_gain, rf_gain, mic_gain, vox_gain, rf_power, nb_val, nr_val, mon_val
        global rx_led, tx_led, hi_swr_led, play_led, rec_led
        global meter_s_val, meter_swr_val, meter_po_val, meter_custom, meter_custom_val

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

        if nb_status == 'ON':
            nb_val_display = str(nb_val).rjust(2,' ')
            self.values['NB_VAL_1'] = nb_val_display[0]
            self.values['NB_VAL_2'] = nb_val_display[1]
        else:
            self.values['NB_VAL_1'] = ' '
            self.values['NB_VAL_2'] = ' '

        if nr_status == 'ON':
            nr_val_display = str(nr_val).rjust(2,' ')
            self.values['NR_VAL_1'] = nr_val_display[0]
            self.values['NR_VAL_2'] = nr_val_display[1]
        else:
            self.values['NR_VAL_1'] = ' '
            self.values['NR_VAL_2'] = ' '

        if mon_status == 'ON':
            mon_val_display = str(mon_val).rjust(2,' ')
            self.values['MON_VAL_1'] = mon_val_display[0]
            self.values['MON_VAL_2'] = mon_val_display[1]
        else:
            self.values['MON_VAL_1'] = ' '
            self.values['MON_VAL_2'] = ' '

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
        if vfo_a_clar_status == 'ON':
            self.values['VFO_A_CLAR_DIRECTION'] = vfo_a_clar_direct
            for i in range(1,5):
                self.values['VFO_A_CLAR_OFFSET_' + str(i)] = vfo_a_clar_offset[i-1]
        else:
            self.values['VFO_A_CLAR_DIRECTION'] = ' '
            for i in range(1,5):
                self.values['VFO_A_CLAR_OFFSET_' + str(i)] = ' '

        if vfo_b_clar_status == 'ON':
            self.values['VFO_B_CLAR_DIRECTION'] = vfo_b_clar_direct
            for i in range(1,5):
                self.values['VFO_B_CLAR_OFFSET_' + str(i)] = vfo_b_clar_offset[i-1]
        else:
            self.values['VFO_B_CLAR_DIRECTION'] = ' '
            for i in range(1,5):
                self.values['VFO_B_CLAR_OFFSET_' + str(i)] = ' '

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

    def render(self):
        """ draw every display part: background, meter, icons, values, buttons, warning """
        self.screen.blit(self.background, (0,0))
        self.sync()
        self.draw_meters()
        self.clock()
        self.draw_icons()
        self.draw_values()
        self.draw_buttons()
        self.draw_warning()
        pygame.display.update()

def main():
    pygame.init()
    # pygame.mouse.set_visible(False)

    # match maximum resolution
    all_support_display_modes = pygame.display.list_modes()
    if (640,480) in all_support_display_modes:
        screen_resolution = 'VGA'
    elif (480,320) in all_support_display_modes:
        screen_resolution = 'HVGA'
    else:
        print 'UNSUPPORTED RESOLUTION. (Only VGA or HVGA)'
        exit()

    with open('conf/custom.yaml','r') as f:
        custome_config = yaml.load(f)
        model = custome_config['RADIO']['MODEL']
        port = custome_config['RADIO']['PORT']
        baudrate = custome_config['RADIO']['BAUDRATE']
        dp_mode = FULLSCREEN if custome_config['RADIO']['FULLSCREEN'] else 0

    # for debug
    # screen_resolution = 'HVGA'
    dp_mode = FULLSCREEN

    # set fps clock, limit fps
    FPS = 20
    fpsClock = pygame.time.Clock()

    rc = Remote_Controller(model=model, resolution=screen_resolution, display_mode=dp_mode)
    rc.init_resouce()
    rc.init_button()

    # start daemon threading for rig status polling
    poll = Rig_Polling(model)
    poll.setDaemon(True)
    poll.start()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                exit()
            elif MOUSEBUTTONDOWN or event.type == MOUSEBUTTONUP:
                x, y = pygame.mouse.get_pos()
                rc.test_buttons(x, y, event.type)

        rc.render()
        fpsClock.tick(FPS)

if __name__ == '__main__':
    main()
