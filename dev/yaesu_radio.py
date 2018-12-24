# -*- coding: utf-8 -*-

'''
@author: Han Jiansheng <BI3QXJ>
@note: Class for FT-891/450/991/DX serial radio's CAT controlling

@TODO: EX instruction not implemented
@TODO: repeater, CTCSS not implemented
@TODO: playback
@TODO: Speech processor
@TODO: PLL
'''

import os
import sys
import re
import time
import yaml
import pyudev
import serial

# # supported device which plug in and detected by os.
# SUPPORTED_DEVICE = [
#     ('10c4','CP2105_Dual_USB_to_UART_Bridge_Controller'),   # FT-891: cp2105 USB-UART module
# ]

# # yaesu rigs model, fetch by id command.
# SUPPORTED_MODELS = {
#     '0650': 'FT-891',
#     '0241': 'FT-450',
#     '0244': 'FT-450D',
#     '0670': 'FT-991A',
#     '0251': 'FT-2000',
#     '0252': 'FT-2000D',
#     '0582': 'FTDX1200(FFT-1)',
#     '0583': 'FTDX1200',
#     'XXXX': 'FTDX3000',
#     '0362': 'FTDX5000',
#     '0101': 'FTDX9000D',
#     '0102': 'FTDX9000Contest',
#     '0103': 'FTDX9000MP'
# }

class RIG(serial.Serial, object):
    ''' Class for Yaesu FT450/891/991/2000/DX Series Radio CAT Operation '''
    
    def __init__(self, baudrate=38400):
        ''' 
        Class init: get device and model, prepare attribute for rig  
        '''
        dev = self.get_compatible_device()
        if dev is None:
            sys.exit('No compatible radio was found.')
        
        model = self.get_radio_model(dev)
        if model is None:
            sys.exit('No compatible radio was found. Make sure your rig is power on.')
        self.model = model

        with open('yaesu_instruction.yaml','r') as f:
            self.__instruction = yaml.load(f)[self.model]
        with open('yaesu_constant.yaml','r') as f:
            self.__constant = yaml.load(f)[self.model]

        self.vfo_a = ''
        self.vfo_b = ''

        super(RIG, self).__init__(
            port=dev.get('DEVNAME'),
            baudrate=38400,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            write_timeout=1,
            timeout=0.1
        )

    ## >>>>>>>>>>>>>>>>>>>>>>>> Device Connection Function <<<<<<<<<<<<<<<<<<<<<<<<
    def get_compatible_device(self):
        '''
        find compatible yaesu radio device
        '''
        cont = pyudev.Context()
        for dev in cont.list_devices():
            if dev.get('ID_VENDOR_ID') is not None and dev.get('ID_MODEL') is not None:
                print '[%s:%s:%s]\n  >%s:%s' % (
                    dev.get('ID_VENDOR_ID',''), 
                    dev.get('ID_MODEL_ID',''), 
                    dev.get('SUBSYSTEM',''), 
                    dev.get('DEVNAME',''), 
                    dev.get('ID_MODEL','')
                )
            if (dev.get('ID_VENDOR_ID'), dev.get('ID_MODEL')) in SUPPORTED_DEVICE:
                if dev.get('SUBSYSTEM') == 'tty':
                    if not os.access(dev.get('DEVNAME', ''), os.W_OK):
                        print 'Found a compatible radio, but can not write to it.'
                    else:
                        return dev
                else:
                    print 'Found a compatible radio, but no serial tty.\nPlease run the following commands with root privileges:\n' + \
                        'modprobe usbserial vendor=0x%s product=0x%s' % (dev.get('ID_VENDOR_ID'), dev.get('ID_MODEL_ID'))
                        
    def get_radio_model(self, dev):
        '''
        Get model of Yaesu Radio, check in supported rig list.
        @TODO: power on when initialization
        '''
        # model = 'FT-891'
        sp = serial.Serial(
            port=dev.get('DEVNAME'),
            baudrate=38400,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            write_timeout=0.1,
            timeout=0.1
        )
        sp.write('ID;')
        dev_id = sp.read(7)[2:6]
        model = SUPPORTED_MODELS.get(dev_id)
        if model:
            print 'Radio connected: %s' % model
            return model
        sp.flush()
        sp.close()
    
    ## >>>>>>>>>>>>>>>>>>>>>>>> Serial Port Operation Function <<<<<<<<<<<<<<<<<<<<<<<<
    def cmd_set(self, command):
        ''' send command (SET) '''
        print 'SET: %s' % command
        self.write(command.encode('utf-8'))
        return
    
    def cmd_read(self, command):
        ''' send command (READ) '''
        print 'READ: %s' % command
        self.write(command.encode('utf-8'))
        line = ''
        while True:
            c = self.read(1)
            if c == ';':
                if line == '?':
                    return 'ERROR'
                else:
                    line = line + ';'
                    print 'ANSR: %s' % line
                    break
            line = line + c
        return line
    
    def cmd_check(self, command):
        ''' check command syntax '''
        if re.match(r'^[A-Z][A-Z](\w|\+|-)*;$', command):
            return True
        else:
            return False

    def send(self, command, oper_type=None, skip_check=False):
        '''
        send command, choose whether read or set automatically
        type: choose read or set manually
        '''
        if not skip_check and not self.cmd_check(command):
            print 'INVALID COMMAND SYNTAX'
            return

        cmd_oper = {'SET': self.cmd_set, 'READ': self.cmd_read}
        if oper_type is None:
            # choose by default instructions dict
            ins_type = command[:2]
            if self.__instruction.has_key(ins_type):
                for k,v in self.__instruction[ins_type].iteritems():
                    if k in ('SET','READ'):
                        if re.match(v, command):    # try to match one of SET/READ
                            return cmd_oper[k](command)
                return 'UNSUPPORTED PARAMETER'
            else:
                return 'UNSUPPORTED COMMAND'
        elif oper_type.upper() in ('READ', 'SET'):
            # choose by user
            return cmd_oper[k](command)
        else:
            print 'UNSUPPORTED CMD_TYPE'

    ## >>>>>>>>>>>>>>>>>>>>>>>> Radio System Function <<<<<<<<<<<<<<<<<<<<<<<<
    
    # not finish
    def check_freq(self, freq, is_amateur=False):
        ''' check frequency within legal range or amateur radio band range '''
        freq_chk = int(freq)    # .rjust(9,'0')
        if not is_amateur and (freq_chk > 56000000 or freq_chk < 30000):     # 30k~56MHz
            return False
        elif is_amateur:
            pass
        else:
            return True
    
    # not finish
    def info(self, val=None):
        '''
        get radio infomation about tx/rx/play/rec/hi-swr/rx_busy
        GET:
            info()      :return {}
            info('TX_LED')  :return TX_LED status
        '''
        if val is None:
            return {
                'TX_LED': self.send(self.__constant['info']['READ']['TX_LED'])
                ,'RX_LED': self.send(self.__constant['info']['READ']['RX_LED'])
                ,'HI_SWR': self.send(self.__constant['info']['READ']['HI_SWR'])
                ,'REC': self.send(self.__constant['info']['READ']['REC'])
                ,'PLAY': self.send(self.__constant['info']['READ']['PLAY'])
                ,'RX_BUSY': self.send(self.__constant['info']['READ']['RX_BUSY'])
            }
        elif self.__constant['info']['READ'].has_key(val.upper()):
            ret_val = self.send(self.__constant['info']['READ'][val])
            return
    
    def key_oper(self, key_name, dup_times=1):
        '''
        set key pressed, include: 
        DIAL_UP, DIAL_DOWN, MULTI_UP, MULTI_DOWN,
        ENTER, BAND_UP, BAND_DOWN, UP, DOWN
        SET:
          send_key('DIAL_UP/MULTI_UP',100)
          send_key('DIAL_UP')   # send once

        '''
        if key_name.upper() not in ('DIAL_UP','DIAL_DOWN','MULTI_UP','MULTI_DOWN','ENTER','DOWN','UP','BAND_UP','BAND_DOWN'):
            print 'SEND_KEY: INVALID KEY'
        elif key_name.upper() not in ('DIAL_UP','DIAL_DOWN','MULTI_UP','MULTI_DOWN') and dup_times <> 1:
            print 'SEND_KEY: ONLY DIAL OR MULTI CAN USE dup_times'
        elif key_name.upper() in ('DIAL_UP','DIAL_DOWN','MULTI_UP','MULTI_DOWN') and dup_times not in range(100):
            print 'SEND_KEY: OUT OF RANGE,(1~99)'
        else:
            key_cmd = self.__constant['key'][key_name.upper()].replace('nn',str(dup_times).rjust(2,'0'))
            self.send(key_cmd)

    def lock(self, val=None):
        '''
        get/set VFO DIAL lock
        GET: lock()
          return: str lock_status 1/0=Locked/Unlocked
        SET: lock('OFF'/'ON')
          return: str lock_status 1/0=Locked/Unlocked
        '''
        if val is None:
            ret_val = self.send(self.__constant['lock']['READ'])
            if self.__constant['lock']['ANSWER'].has_key(ret_val):
                return self.__constant['lock']['ANSWER'][ret_val]
            else:
                print 'FAIL'
        elif self.__constant['lock']['SET'].has_key(val.upper()):
            self.send(self.__constant['lock']['SET'][val.upper()])
            return self.lock()
        else:
            print 'LOCK: INVALID PARAMETER'

    # not finish
    def power(self, val=None):
        '''
        get/set Power status
        GET: power()
          return str power_status
        SET: power('ON'/'OFF')
          return str power_status
        '''
        pass

    ## >>>>>>>>>>>>>>>>>>>>>>>> Radio Function <<<<<<<<<<<<<<<<<<<<<<<<
    

    def af_gain(self, val=None):
        '''
        get/set AF Gain
        GET: af_gain()
          return: int af_gain
        SET: af_gain(0~255)
          return: int af_gain
        '''
        if val is None:
            ret_val = self.send(self.__constant['af_gain']['READ'])
            return int(ret_val[3:-1])
        elif val in range(0, 256):
            self.send(self.__constant['af_gain']['SET'].replace('nnn', str(val).rjust(3,'0')))
            return self.af_gain()
        else:
            print 'AF_GAIN: OUT OF RANGE'

    def agc(self, val=None):
        '''
        get/set agc function
        GET: agc()
          return: str agc_type: 'OFF'/'FAST'/'MID'/'SLOW'/'AUTO-FAST'/'AUTO-MID'/'AUTO-SLOW'
        SET: agc('OFF'/'FAST'/'MID'/'SLOW'/'AUTO')
          return: str agc_type
        '''
        if val is None:
            ret_val = self.send(self.__constant['agc']['READ'])
            if self.__constant['agc']['ANSWER'].has_key(ret_val):
                return self.__constant['agc']['ANSWER'][ret_val]
            else:
                return 'FAIL'
        elif self.__constant['agc']['SET'].has_key(val.upper()):
            self.send(self.__constant['agc']['SET'][val.upper()])
            return self.agc()
        else:
            print 'AGC: INVALID PARAMETER'

    def apf(self, status=None, freq=None):
        pass

    def att(self, val=None):
        '''
        get/set RF Attenuator
        GET: att()
          return: str att_status: 'OFF'/'ON'
        SET: att('OFF'/'ON')
          return: str att_status
        '''
        if val is None:
            ret_val = self.send(self.__constant['att']['READ'])
            if self.__constant['att']['ANSWER'].has_key(ret_val):
                return self.__constant['att']['ANSWER'][ret_val]
            else:
                return 'FAIL'
        elif self.__constant['att']['SET'].has_key(val.upper()):
            self.send(self.__constant['att']['SET'][val.upper()])
            return self.att()
        else:
            print 'ATT: INVALID PARAMETER'

    def atu(self, val=None):
        '''
        get/set Antenna Tuner status
        GET: atu()
          return: str atu_status: 'OFF'/'ON'/'TUNING'
        SET: atu('OFF'/'ON'/'TUNING')
          return: str atu_status
        '''

        # error with 'AC;'-'ERROR;' when no atu attached
        if val is None:
            ret_val = self.send(self.__constant['atu']['READ'])
            if self.__constant['atu']['ANSWER'].has_key(ret_val):
                return self.__constant['atu']['ANSWER'][ret_val]
            else:
                print 'FAIL'
        elif self.__constant['atu']['SET'].has_key(val.upper()):
            self.send(self.__constant['atu']['SET'][val.upper()])
            return self.atu()
        else:
            print 'ATU: INVALID PARAMETER'
    
    def atu_select(self, val=None):
        '''
        get/set Antenna Tuner type
        GET: atu_select()
          return: str atu_type: 'EXT'/'ATAS'/'LAMP'
        SET: atu_select('EXT'/'ATAS'/'LAMP')
          return: str atu_type
        '''
        if val is None:
            ret_val = self.send(self.__constant['atu']['SELECT']['READ'])
            if self.__constant['atu']['SELECT']['ANSWER'].has_key(ret_val):
                return self.__constant['atu']['SELECT']['ANSWER'][ret_val]
            else:
                print 'FAIL'
        elif self.__constant['atu']['SELECT']['SET'].has_key(val.upper()):
            self.send(self.__constant['atu']['SELECT']['SET'][val.upper()])
            return self.atu_select()
        else:
            print 'ATU_SELECT: INVALID PARAMETER'

    def band(self, val):
        '''
        set band of radio
        SET: band(10)   # switch to 10m band
             band(7M)   # switch to 7MHz band
        '''
        if self.__constant['band'].has_key(val):
            self.send(self.__constant['band'][val])
        else:
            print 'BAND: BAND ERROR'
    
    # when not in cw mode, send 'BI1;' command will turn on and off bk, but always returns 'BI0;' 
    def bk_in(self, val=None):
        '''
        get/set CW Break-In
        GET: break_in()
          return: str break_in: 'ON'/'OFF'
        SET: break_in('ON'/'OFF')
          return: str atu_type
        '''
        if val is None:
            ret_val = self.send(self.__constant['cw']['break_in']['READ'])
            if self.__constant['cw']['break_in']['ANSWER'].has_key(ret_val):
                return self.__constant['cw']['break_in']['ANSWER'][ret_val]
            else:
                print 'FAIL'
        elif self.__constant['cw']['break_in']['SET'].has_key(val.upper()):
            self.send(self.__constant['cw']['break_in']['SET'][val.upper()])
            return self.bk_in()
        else:
            print 'BK-IN: INVALID PARAMETER'

    def bk_in_type(self, val=None):
        pass
    
    def bk_in_delay(self, val=None):
        pass

    def channel(self, val=None):
        '''
        get/set memory channel
        MC;
        '''

    def channel_read(self, val=None):
        pass

    def channel_write(self, p1=None, p2=None, p3=None):
        pass

    def clar(self, val=None):
        '''
        get/set CLAR status
        GET:
          clar()
          return: ('ON'|'OFF', offset)
          clar()
          RU;RD;RC
        '''
        pass

    def clar_offset(self, val=0):
        pass

    def clar_clear(self):
        pass

    def contour(self, status=None, freq=None):
        pass

    def cw_bk_delay(self, val=None):
        pass

    def cw_keyer(self, val=None):
        pass

    def cw_keying(self, val=None):
        pass
    
    def cw_pitch(self, val=None):
        pass

    def cw_speed(self, val=None):
        pass

    def cw_spot(self, length=None, interval=None):
        ''' cw tx '''
        pass

    def dimmer(self, contrast=None, key=None, lcd=None, led=None):
        '''
        get/set dimmer setting
        GET: dimmer()
          return {
              contrast: int x, key: int y, lcd: int m, led: int n
          }
        SET: dimmer(LCD=8)
        '''
        ret_val = self.send('DA;')
        contrast_val = str(contrast).rjust(2,'0') if contrast in range(1,16) else ret_val[2:4]
        key_value = str(key).rjust(2,'0') if key in range(1,16) else ret_val[4:6]
        lcd_value = str(lcd).rjust(2,'0') if lcd in range(1,16) else ret_val[6:8]
        led_value = str(led).rjust(2,'0') if led in range(1,16) else ret_val[8:10]
        dimmer_str = contrast_val+key_value+lcd_value+led_value

        if dimmer_str <> ret_val[2:10]:
            self.send('DA' + dimmer_str + ';')
        else:
            return {
                'contrast': int(ret_val[2:4]),
                'key': int(ret_val[4:6]),
                'lcd': int(ret_val[6:8]),
                'led': int(ret_val[8:10]),
            }

    def fast(self, val=None):
        '''
        get/set fast status
        GET: fast()
          return: str fast_status
        SET: fast('OFF'/'ON')
          return: str fast_status
        '''
        if val is None:
            ret_val = self.send(self.__constant['fast']['READ'])
            return self.__constant['fast']['ANSWER'][ret_val]
        elif self.__constant['fast']['SET'].has_key(val.upper()):
            self.send(self.__constant['fast']['SET'][val.upper()])
            return self.fast()
        else:
            print 'FAST: INVALID PARAMETER'

    def if_shift(self,status=None, shift=None):
        pass

    def ipo(self, val=None):
        '''
        get/set RF Pre-AMP
        GET: ipo()
          return: str ipo_status: 'OFF'/'ON'
        SET: ipo('OFF'/'ON')
          return: str ipo_status
        '''
        if val is None:
            ret_val = self.send(self.__constant['ipo']['READ'])
            if self.__constant['ipo']['ANSWER'].has_key(ret_val):
                return self.__constant['ipo']['ANSWER'][ret_val]
            else:
                print 'FAIL'
        elif self.__constant['ipo']['SET'].has_key(val.upper()):
            self.send(self.__constant['ipo']['SET'][val.upper()])
            return self.ipo()
        else:
            print 'IPO: INVALID PARAMETER'

    def load_message(self, val=None):
        ''' load message'''
        pass

    def meter(self, val=None):
        '''
        get meter's readings
        GET: 
          meter()   # return reading on default meter
          meter('ALL') # return {
              'S': int value,
              'COMP': int value,
              'ALC': int value,
              'PO': int value,
              'SWR': int value, # raw value by rig's meter, not real
              'ID': int value
              }
          meter('S'/'PO'/'SWR'/...)
        '''
        if val is None:
            s_val = self.send(self.__constant['meter']['READ']['S'])
            comp_val = self.send(self.__constant['meter']['READ']['COMP'])
            alc_val = self.send(self.__constant['meter']['READ']['ALC'])
            po_val = self.send(self.__constant['meter']['READ']['PO'])
            swr_val = self.send(self.__constant['meter']['READ']['SWR'])
            id_val = self.send(self.__constant['meter']['READ']['ID'])
            return {
                'S': int(s_val[3:-1]),
                'COMP': int(comp_val[3:-1]),
                'ALC': int(alc_val[3:-1]),
                'PO': int(po_val[3:-1]),
                'SWR': int(swr_val[3:-1]),
                'ID': int(id_val[3:-1])
              }
        elif self.__constant['meter']['READ'].has_key(val.upper()):
            ret_val = self.send(self.__constant['meter']['READ'][val.upper()])
            return int(ret_val[3:-1])
        else:
            print 'METER: INVALID PARAMETER'

    def meter_select(self, val=None):
        '''
        get/set meter displayed on panel
        GET: meter_select()
          return str meter_type
        SET: meter_select('COMP'/'ALC'/'PO'/'SWR'/'ID')
          return str meter_type
        '''
        if val is None:
            ret_val = self.send(self.__constant['meter']['SELECT']['READ'])
            if self.__constant['meter']['SELECT']['ANSWER'].has_key(ret_val):
                return self.__constant['meter']['SELECT']['ANSWER'][ret_val]
            else:
                print 'FAIL'
        elif self.__constant['meter']['SELECT']['SET'].has_key(val.upper()):
            self.send(self.__constant['meter']['SELECT']['SET'][val.upper()])
            return self.meter_select()
        else:
            print 'METER_SELECT: INVALID PARAMETER'

    def mic_gain(self, val=None):
        pass

    # 7M-LSB, 14M-USB, can't set USB on 7M
    def mode(self, val=None):
        '''
        get/set hf mode
        GET: mode()
          return: str mode
        SET: mode('LSB'/'USB'/'FM'/'AM'/...)
          return: str mode
        '''
        if val is None:
            ret_val = self.send(self.__constant['mode']['READ'])
            if self.__constant['mode']['ANSWER'].has_key(ret_val):
                return self.__constant['mode']['ANSWER'][ret_val]
            else:
                print 'FAIL'
        elif self.__constant['mode']['SET'].has_key(val.upper()):
            self.send(self.__constant['mode']['SET'][val.upper()])
            return self.mode()
        else:
            print 'MODE: INVALID PARAMETER'

    # new
    def monitor(self, val=None):
        '''
        get/set monitor function
        GET: 
          monitor()
            return: str_status, int mon_level
          monitor('LEVEL')
            return: int mon_level
        SET:
          monitor('OFF'/'ON'/0~100)
            return: str_status, int mon_level
            note: set level do not change status
        '''
        if val is None:
            ret_val = self.send(self.__constant['monitor']['READ'])
            if self.__constant['monitor']['ANSWER'].has_key(ret_val):
                mon_status = self.__constant['monitor']['ANSWER'][ret_val]
            else:
                print 'FAIL'
                return
            mon_level = int(self.send(self.__constant['monitor']['LEVEL']['READ'])[3:-1])
            return mon_status, mon_level
        elif self.__constant['monitor']['SET'].has_key(val.upper()):
            self.send(self.__constant['monitor']['SET'][val.upper()])
            return self.monitor()
        elif val in range(101):
            self.send(self.__constant['monitor']['LEVEL']['SET'].replace('nnn',str(val).rjust(3,'0')))
            return self.monitor()
        else:
            print 'MONITOR: INVALID PARAMETER'
            
    # Transmit activated when ON
    def mox(self, val=None):
        '''
        get/set mox function
        GET: mox()
          return: str mox_status
        SET: mox('ON'/'OFF')
          return: str mox_status
        '''
        if val is None:
            ret_val = self.send(self.__constant['mox']['READ'])
            if self.__constant['mox']['ANSWER'].has_key(ret_val):
                return self.__constant['mox']['ANSWER'][ret_val]
            else:
                print 'FAIL'
        elif self.__constant['mox']['SET'].has_key(val.upper()):
            self.send(self.__constant['mox']['SET'][val.upper()])
            return self.mox()
        else:
            print 'MOX: INVALID PARAMETER'
    
    def narrow(self, val=None):
        '''
        get/set narrow function
        GET: narrow()
          return: str narrow_status
        SET: narrow('ON'/'OFF')
          return: str narrow_status
        '''
        if val is None:
            ret_val = self.send(self.__constant['narrow']['READ'])
            if self.__constant['narrow']['ANSWER'].has_key(ret_val):
                return self.__constant['narrow']['ANSWER'][ret_val]
            else:
                print 'FAIL'
        elif self.__constant['narrow']['SET'].has_key(val.upper()):
            self.send(self.__constant['narrow']['SET'][val.upper()])
            return self.narrow()
        else:
            print 'NARROW: INVALID PARAMETER'
    
    def nb(self, val=None):
        ''' Noise Blanker and level'''
        pass

    def notch(self, mode=None, level=None):
        '''
        get/set NOTCH function status
        GET: notch()
          return: (
              auto_notch_status,
              manual_notch_status,
              manual_notch_level
              )
        SET: 
          notch('AUTO_ON')
          notch('AUTO_OFF')
          notch('MANUAL', 100)
        '''
        pass

    def nr(self, val=None):
        ''' Noise Blanker and level'''
        pass

    def qmb_store(self):
        pass
    def qmb_recall(self):
        pass

    def quick_split(self):
        pass

    def rf_power(self, val=None):
        '''
        get/set RF Power by mode (instead of choose specific item in EX160n 'TX POWER')
        GET: rf_power()
          return: int rf_power()
        SET: rf_power(5~100)
          return: int rf_power()
        '''
        if val is None:
            ret_val = self.send(self.__constant['rf_power']['READ'])
            return int(ret_val[2:-1])
        elif val in range(5, 101):
            self.send(self.__constant['rf_power']['SET'].replace('nnn', str(val).rjust(3,'0')))
            return self.rf_power()
        else:
            print 'RF_POWER: OUT OF RANGE'

    def rf_gain(self, val=None):
        '''
        get/set RF Gain
        GET: rf_gain()
          return: int rf_gain
        SET: rf_gain(0~30)
          return: int rf_gain
        '''
        if val is None:
            ret_val = self.send(self.__constant['rf_gain']['READ'])
            return int(ret_val[3:-1])
        elif val in range(0, 31):
            self.send(self.__constant['rf_gain']['SET'].replace('nnn', str(val).rjust(3,'0')))
            return self.rf_gain()
        else:
            print 'RF_GAIN: OUT OF RANGE'
    def s(self):
        pass

    def scan(self, val=None):
        '''
        SC;
        '''
        pass

    def scope(self, samples=160, step=0.25):
        '''
        scan range of frequency, return list of signal stength.
        USAGE:
        samples: numbser of samplings
        step: sampling step, kHz
        scope(400, 1): get 400 samples every 1kHz.
        '''
        center = self.vfo('A')
        scp_list = []
        low_val = int(center) -  step * 1000 * samples / 2
        for freq in [low_val + step * 1000 * x for x in range(samples+1)]:
            cmd = 'FA'+str(int(freq)).rjust(9,'0')+';'
            print cmd
            self.rig_set(cmd.encode('utf-8'))
            time.sleep(0.015)
            # scp_list.append(int((self.rig_read('SM0;').decode('utf-8')[3:6])))
            scp_list.append(self.meter('S'))
        # print scp_list
        self.vfo('A', center)
        return scp_list
    
    def split(self, val=None):
        pass

    def sql(self, val=None):
        pass

    def tx(self, val=None):
        ''' TX;'''
        pass

    def tx_set(self, radio_tx=None, cat_tx=None):
        pass

    def vfo(self, vfo_to=None, vfo_from=None):
        '''
        get/set VFO-A/B frequency
        GET: vfo('A')   # get vfo-a 
             vfo('B')   # get vfo-b
             return frequency (like '7.050.000', lstrip '0')
        SET: vfo('A','14270000')  # set vfo-a freq
             vfo('B','A')   # vfo-a to vfo-b
             vfo('A','B')   # vfo-b to vfo-a
             vfo('M','A')   # vfo-a to memory channel
             vfo('A','M')   # memory channel to vfo-a
             vfo()          # swap vfo
        '''
        if vfo_from is None and vfo_to is None:
            return self.send('SV;')
        if vfo_to in ('A','B') and vfo_from is None:
            ret_val = self.send('F' + vfo_to + ';')
            return ret_val[2:-1]
        elif vfo_from == 'A' and vfo_to == 'B':
            return self.send('AB;')
        elif vfo_from == 'B' and vfo_to == 'A':
            return self.send('BA;')
        elif vfo_from == 'A' and vfo_to == 'M':
            return self.send('AM;')
        elif vfo_from == 'M' and vfo_to == 'A':
            return self.send('MA;')
        elif vfo_to in ('A','B') and self.check_freq(vfo_from):
            return self.send('F' + vfo_to + str(vfo_from).rjust(9,'0') + ';')
        else:
            print 'VFO: INVALID PARAM'
    
    def vfo_info(self, val=None):
        '''
        get vfo detail
        GET: 
        vfo_info('A','B')
            return: detail info of vfo_a or vfo_b
            {
                P1: xxx # channel no.
                P2: vfo_a frequency
                P3: clar_direction, clar_offset
                P4: clar_status
                P5: 0
                P6: mode
                P7: vfo/memory/MT/QMB/QMB-MT/PMS/HOME
                P8: CTCSS/DCS
                P9: 00
                P10: shift
            }
        vfo_info()
            return: {
                'A': vfo_a dict {} as above
                'B': vfo_b dict {} as above
                }
        '''
        if val is None:
            ret_a = self.vfo_info('A')
            ret_b = self.vfo_info('B')
            return {'A':ret_a, 'B':ret_b}
        elif self.__constant['vfo_info']['READ'].has_key(val.upper()):
            ret_val = self.send(self.__constant['vfo_info']['READ'][val.upper()])
            p1 = ret_val[2:5]
            p2 = ret_val[5:14]
            p3 = ret_val[14:19]
            p4 = self.__constant['vfo_info']['ANSWER']['CLAR'][ret_val[19:20]]
            p6 = self.__constant['vfo_info']['ANSWER']['MODE'][ret_val[21:22]]
            p7 = self.__constant['vfo_info']['ANSWER']['CHANNEL'][ret_val[22:23]]
            p8 = ret_val[23:24]
            p10 = ret_val[26:27]
            return {
                'ch_num': p1,
                'freq': p2,
                'clar_offset': p3,
                'clar_status': p4,
                'mode': p6,
                'vm_type': p7,
                'ctcss': p8,
                'shift': p10
            }
        else:
            print 'VFO_INFO: INVALID PARAMETER'
    
    def vox(self, status=None, delay=None, gain=None):
        pass
        
    def vox_delay(self):
        pass

    def vox_gain(self):
        pass

    def width(self, val=None):
        pass

    def zero_in(self):
        pass