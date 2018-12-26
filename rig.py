# -*- coding: utf-8 -*-

'''
@author: Han Jiansheng <BI3QXJ>
@note: 
'''
import yaml
import serial

# class COMMON_RIG(serial.Serial, object):
#     def __init__(self, port=None, baudrate=38400):
#         super(COMMON_RIG, self).__init__(
#             port=port,
#             baudrate=38400,
#             bytesize=serial.EIGHTBITS,
#             parity=serial.PARITY_NONE,
#             stopbits=serial.STOPBITS_ONE,
#             write_timeout=1,
#             timeout=0.1
#         )
#     def cmd_w(self, command):
#         raise NotImplementedError
#     def cmd_r(self, command):
#         raise NotImplementedError
#     def cmd_wr(self, command, length, stop_char, error_char):
#         raise NotImplementedError

class YAESU_CAT3(serial.Serial, object):
    def __init__(self, model='', port='/dev/ttyUSB0', baudrate=9600):
        super(YAESU_CAT3, self).__init__(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            write_timeout=1,
            timeout=0.1
        )
        with open('conf/YAESU_CAT3.yaml','r') as f:
            self.__func = yaml.load(f)[model]

    def cmd_r(self, command):
        # print 'READ: %s' % command
        self.write(command.encode('utf-8'))
        line = ''
        while True:
            c = self.read(1)
            if c == ';':
                if line == '?':
                    return 'ERROR'
                else:
                    line = line + ';'
                    # print 'ANSR: %s' % line
                    break
            line = line + c
        return line

    def cmd_w(self, command):
        # print 'SET: %s' % command
        self.write(command.encode('utf-8'))
        return

    def func(self, func_name, **kwargs):
        # print '[FUNC_EXEC@%s]: %s' % (func_name[-3:], func_name)

        if self.__func.has_key(func_name):  # 检查配置文件中是否有该指令
            if func_name.endswith('_GET'):
                cmd_ret = {}
                ret = self.cmd_r(self.__func[func_name]['CMD'])
                for k,v in self.__func[func_name]['RET'].iteritems():
                    ret_seg = ret[eval(v)[0]:eval(v)[1]]
                    if self.__func[func_name]['DIM'] is not None and self.__func[func_name]['DIM'].has_key(k):
                        cmd_ret[k] = self.__func[func_name]['DIM'][k].get(ret_seg, 'UNKNOWN')
                    elif self.__func[func_name]['CONVERT'] is not None and self.__func[func_name]['CONVERT'].has_key(k):
                        cmd_ret[k] = int(round(eval(self.__func[func_name]['CONVERT'][k].replace('x', str(int(ret_seg))))))
                    else:
                        cmd_ret[k] = ret_seg
                return cmd_ret
            elif func_name.endswith('_SET'):  
                command = self.__func[func_name]['CMD']
                for k,v in kwargs.iteritems():  # 将函数入参转换格式后进行替换
                    if self.__func[func_name]['DIM'] is not None and self.__func[func_name]['DIM'].has_key(k):
                        command = command.replace('{$'+k+'}', self.__func[func_name]['DIM'][k][v])
                    elif self.__func[func_name]['CONVERT'] is not None and self.__func[func_name]['CONVERT'].has_key(k):
                        conv_val = int(round(eval(self.__func[func_name]['CONVERT'][k]['EXPS'].replace('x', str(v)))))
                        form = self.__func[func_name]['CONVERT'][k]['FORM'].split('|')
                        if form[0] == 'L':
                            var_str = str(conv_val).ljust(int(form[1]), form[2])
                        elif form[0] == 'R':
                            var_str = str(conv_val).rjust(int(form[1]), form[2])
                        else:
                            var_str = str(conv_val)
                        command = command.replace('{$'+k+'}', var_str)
                    else:
                        command = command.replace('{$'+k+'}', v)
                self.cmd_w(command)  # 发送命令
            else:
                print '[FUNC_EXEC]: UNKNOWN TYPE - %s' % func_name
        else:
            print '[FUNC_EXEC]: NOT SUPPORT - %s' % func_name
    
    def button_func(self, button_command, **kwargs):
        pass

    ############################ GAIN ############################
    def af_gain_set(self, val):
        return self.func('AF_GAIN_SET', VAL=val)

    def af_gain_get(self):
        return self.func('AF_GAIN_GET')
    
    def rf_gain_get(self):
        return self.func('RF_GAIN_GET')
    
    def mic_gain_get(self):
        return self.func('MIC_GAIN_GET')
    
    def vox_gain_get(self):
        return self.func('VOX_GAIN_GET')
    ############################/ GAIN ############################

    def agc_get(self):
        return self.func('AGC_GET')

    def att_get(self):
        return self.func('ATT_GET')
    
    def bkin_get(self):
        return self.func('BREAK_IN_GET')
    
    def contour_get(self):
        return self.func('CONTOUR_GET')
    
    def ipo_get(self):
        return self.func('IPO_GET')
    
    def monitor_get(self):
        return self.func('MONITOR_GET')
    
    def narrow_get(self):
        return self.func('NARROW_GET')
    
    def nb_get(self):
        return self.func('NB_GET')

    def nr_get(self):
        return self.func('NR_GET')

    def prc_get(self):
        return self.func('SPEECH_PROCESSOR_GET')

    def shift_get(self):
        return self.func('IF_SHIFT_GET')
    
    def split_get(self):
        return self.func('SPLIT_GET')
    
    def atu_get(self):
        return self.func('ATU_GET')
    
    def vox_get(self):
        return self.func('VOX_GET')

    ############################ VFO ############################
    def vfo_a_b(self):
        return self.func('VFO_A_B_SET')

    def vfo_freq(self, vfo):
        if vfo == 'A':
            return self.func('VFO_A_FREQ_GET')
        elif vfo == 'B':
            return self.func('VFO_B_FREQ_GET')
    
    def vfo_info(self, vfo):
        if vfo == 'A':
            return self.func('VFO_A_GET')
        elif vfo == 'B':
            return self.func('VFO_B_GET')
    ############################/ VFO ############################
    def meter(self, meter_select):
        if meter_select == 'S':
            return self.func('METER_S_GET')
        elif meter_select == 'SWR':
            return self.func('METER_SWR_GET')
        elif meter_select == 'PO':
            return self.func('METER_PO_GET')

class FT891(YAESU_CAT3, object):
    def __init__(self):
        print 'You get a FT891'
        super(FT891, self).__init__(
            model='FT-891'
            ,port='/dev/ttyUSB0'
            ,baudrate=38400
        )
    

class RIG(object):
    def connect(self, model):
        model_list = {
            'YAESU': YAESU_CAT3
            ,'FT-891': FT891
        }
        return model_list[model]()

# f = RIG()
# a = f.create('FT891')
# b = f.create('FT450')

# a.af_gain_set(1)
# a.af_gain_get()
# b.af_gain_set(1)
# b.af_gain_get()
