
import re
import time
import sys
import json
import os
from src.wifiSpeaker.AseInfo import AseInfo
from src.common.Logger import Logger
from src.common.relay import Relay


class Automate(object):

    def __init__(self, cfg, state_path, socketio=None):
        cfg.cfg_load()
        self.cfg = cfg.cfg
        self.ase_info = AseInfo()
        self.socketio = socketio
        self.state_path = os.path.abspath(state_path)
        self.button = Relay()
        self.ac_power = Relay()
        self.bp_relay_init = None
        self.log = Logger("automate").logger()

    def print_log(self, info, color='white'):
        try:
            self.log.info(info)
            self.socketio.sleep(0.02)   # Avoid sockeit network block leads to cannot print on page
            self.socketio.emit('print_msg',
                               {'data': info, 'color': color},
                               namespace='/automate/test')
        except Exception as e:
            self.log.debug("Error when print_log: {}".format(e))
            sys.exit()

    def delay(self, t):
        if self.socketio is not None:
            self.socketio.sleep(t)
        else:
            time.sleep(t)

    @staticmethod
    def _split(para):
        info = []
        if ',' in para:
            values = re.findall('[^()]+', para)[1].split(',')
            for v in values:
                info.append(v.split(':')[1])
        else:
            values = re.findall('[^()]+', para)[1].split(':')[1]
            info.append(values)
        return info

    def get_ase_info(self, name):
        ip = self.cfg.get('ASE', 'ip')
        info = self.ase_info.get_info(name, ip)
        if info == 'error' or info == 'NA':
            self.print_log('Seems disconnected with your product!', 'red')
            return False
        return info

    def do_check(self, name, name_exp, name_get):
        name_exp = self._split(name_exp)[0]
        if str(name_exp).lower() != str(name_get).lower():
            self.print_log('Current {}[{}] is unequal with expected[{}]'.format(name, name_get, name_exp), 'red')
            return False
        else:
            self.print_log('Checked current {} = {}'.format(name, name_get))
        return True

    def send_command(self, cmd):
        ip = self.cfg.get('ASE', 'ip')
        playback = ['Pause', 'Play']
        self.print_log('Send {} --> {}'.format(cmd, ip))
        if cmd in playback and self.ase_info.stream(ip, cmd) == 200:
            self.delay(1)
            return True
        elif cmd == 'Standby' and self.ase_info.standby(ip) == 200:
            return True
        self.print_log('Seems disconnected with your product!', 'red')
        return False

    def send_pause(self):
        if not self.send_command('Pause'):
            return False
        return True

    def send_play(self):
        if not self.send_command('Play'):
            return False
        return True

    def set_standby(self):
        if not self.send_command('Standby'):
            return False
        return True

    def set_volume(self, steps_para):
        ip = self.cfg.get('ASE', 'ip')
        value = self._split(steps_para)[0]
        self.print_log('Set volume to {}'.format(value))
        if self.ase_info.set_volume(ip, value) != 200:
            self.print_log('Seems disconnected with your product!', 'red')
            return False
        return True

    def do_check_network(self, steps_para):
        ip = self.cfg.get('ASE', 'ip')
        value = self._split(steps_para)[0].lower()
        beo_device = self.ase_info.get_info('BeoDevice', ip)
        if beo_device == 'error' and value == 'no':
            self.print_log('Current network is off')
        elif beo_device != 'error' and value == 'yes':
            self.print_log('Current network is on')
        else:
            self.print_log('Current network is not [{}]'.format(value), 'red')
            return False
        return True

    def do_check_volume(self, steps_para):
        volume_info = self.get_ase_info('volume')
        if volume_info is False:
            return False
        vol_get = volume_info.get('Current Level')
        if not self.do_check('volume', steps_para, vol_get):
            return False
        return True

    def do_check_playback(self, steps_para):
        stream_info = self.get_ase_info('stream_state')
        if stream_info is False:
            return False
        current_state = stream_info.get('state').lower()
        #   stream_info.get('source_type')
        if not self.do_check('playback', steps_para, current_state):
            return False
        return True

    def do_check_source(self, steps_para):
        source = self.get_ase_info('current_source')
        if source is False:
            return False
        if not self.do_check('source', steps_para, source.lower()):
            return False
        return True

    def do_check_power_state(self, steps_para):
        standby = self.get_ase_info('get_standby')
        if standby is False:
            return False
        if not self.do_check('power state', steps_para, standby.lower()):
            return False
        return True

    def do_check_bt_connection(self, steps_para):
        bt_setting = self.get_ase_info('bluetoothSettings')
        if bt_setting is False:
            return False
        bt_devices = bt_setting.get('bt_devices')
        state = 'no'
        if len(bt_devices) > 0:
            for d in bt_devices:
                if d.get('connected'):
                    self.print_log('BT connected device: [{}]'.format(d.get('deviceName')))
                    state = 'yes'
                    break
        if not self.do_check('BT connection', steps_para, state):
            return False
        return True

    def button_press(self, steps_para):
        if self.bp_relay_init:
            values = self._split(steps_para)
            key = values[0]
            t = values[1]
            key = key.split('&') if '&' in key else [key]
            self.print_log(steps_para)
            self.button.press(key, t)
        else:
            self.print_log('Something wrong with your relay!', 'red')
            return False
        return True

    def _ac_power(self, steps_para):
        state = self._split(steps_para)[0]
        if not self.ac_power.ac_power(state):
            self.print_log('Something wrong with your Relay!!!', 'red')
            return False
        self.print_log(steps_para)
        return True

    def process_steps(self, steps):
        for i in range(1, len(steps)):
            with open(self.state_path) as f:
                status_running = json.load(f)
            if status_running["run_state"] == 0:
                self.socketio.emit("stop_confirm", namespace='/automate/test')
                sys.exit()
            action = steps[str(i)]
            for k, v in action.items():
                if k == 'send_pause':
                    if not self.send_pause():
                        return False
                elif k == 'send_play':
                    if not self.send_play():
                        return False
                elif k == 'set_standby':
                    if not self.set_standby():
                        return False
                elif k == 'delay':
                    t = self._split(v)[0]
                    self.print_log('Delay {} s'.format(t))
                    self.delay(float(t))
                elif k == 'set_volume':
                    if not self.set_volume(v):
                        return False
                elif k == 'do_check_network':
                    if not self.do_check_network(v):
                        return False
                elif k == 'do_check_volume':
                    if not self.do_check_volume(v):
                        return False
                elif k == 'do_check_playback':
                    if not self.do_check_playback(v):
                        return False
                elif k == 'do_check_source':
                    if not self.do_check_source(v):
                        return False
                elif k == 'do_check_power_state':
                    if not self.do_check_power_state(v):
                        return False
                elif k == 'do_check_bt_connection':
                    if not self.do_check_bt_connection(v):
                        return False
                elif k == 'button_press':
                    if not self.button_press(v):
                        return False
                elif k == 'ac_power':
                    if not self._ac_power(v):
                        return False
        return True

    def run(self, steps):
        total_times = int(steps['total_times'])
        for x in steps:
            if 'button_press' in steps[x]:
                usb_port = 'com' + self.cfg.get('Button_Press', 'bp_usb_port')
                self.button.init_relay(usb_port)
                self.bp_relay_init = self.button.init_button()
            elif 'ac_power' in steps[x]:
                usb_port = 'com' + self.cfg.get('AC_Power', 'ac_usb_port')
                self.ac_power.init_relay(usb_port)
        c_time = 0
        while c_time < total_times:
            c_time += 1
            txt = '**************This is the {} times**************'.format(c_time)
            self.print_log(txt)
            self.socketio.emit("show_running_info", {'current_times': c_time}, namespace='/automate/test')
            if not self.process_steps(steps):
                self.delay(0.2)
                self.socketio.emit("run_stopped", namespace='/automate/test')
                break
        if c_time >= total_times:
            self.socketio.emit('running_over', namespace='/automate/test')