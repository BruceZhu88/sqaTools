
import sys
import json
import random
import os
from time import sleep
from serial.tools import list_ports
from src.common.Logger import Logger
from src.common.SerialHelper import SerialHelper


class SerialTool(object):
    def __init__(self, state_path, socketio=None):
        self.socketio = socketio
        self.log = Logger("power_cycle").logger()
        self.ini = None
        self.port_list = []
        self.ser = None
        self.port_selected = None
        self.port_disconnect = False
        self.state_path = os.path.abspath(state_path)

    def print_log(self, msg, color='white'):
        try:
            self.log.info(msg)
            if self.socketio is not None:
                self.socketio.sleep(0.01)   # Avoid sockeit network block leads to cannot print on page
                self.socketio.emit('print_log',
                                   {'msg': msg, 'color': color},
                                   namespace='/power_cycle/test')
        except Exception as e:
            self.log.debug("Error when print_log: {}".format(e))
            sys.exit()

    def add_port(self, port_info):
        try:
            self.socketio.sleep(0.005)
            self.socketio.emit('add_port',
                               {'data': port_info},
                               namespace='/power_cycle/test')
        except Exception as e:
            self.log.debug("Error when add_port: {}".format(e))
            sys.exit()

    def del_port(self, port_info):
        try:
            self.socketio.sleep(0.005)
            self.socketio.emit('del_port',
                               {'data': port_info},
                               namespace='/power_cycle/test')
        except Exception as e:
            self.log.debug("Error when del_port: {}".format(e))
            sys.exit()

    def delay(self, t):
        if self.socketio is not None:
            self.socketio.sleep(t)
        else:
            sleep(t)

    def find_all_serial(self):
        """Get serial list
        :param self:
        :return:
        """
        try:
            temp_serial = list()
            for com in list_ports.comports():
                str_com = com[0] + ": " + com[1][:-7]  # + ": " + com[1][:-7].decode("gbk").encode("utf-8")
                temp_serial.append(str_com)
            for item in temp_serial:
                if item not in self.port_list:
                    self.add_port(item)
                    self.port_list.append(item)
            for item in self.port_list:
                if item not in temp_serial:
                    self.port_list = [i for i in filter(lambda x: x != item, self.port_list)]
                    self.del_port(item)
            self.port_list = temp_serial
            if self.port_selected is not None:
                if self.port_selected not in self.port_list:
                    self.port_disconnect = True
                    msg = "Disconnected [{0}]!".format(self.port_selected)
                    self.socketio.emit('port_status', {'msg': msg, 'color': "red"}, namespace='/power_cycle/test')
                    self.port_selected = None
        except Exception as e:
            self.log.error(e)
            sys.exit()

    def open_port(self, port_set):
        try:
            self.port_selected = port_set["port_info"]
            port = port_set["port_info"].split(":")[0]
            baud_rate = port_set["baud_rate"]
            parity = port_set["parity"]
            data_bit = port_set["data_bit"]
            stop_bit = port_set["stop_bit"]
            self.ser = SerialHelper(Port=port, BaudRate=baud_rate, ByteSize=data_bit, Parity=parity, Stopbits=stop_bit)
            self.ser.start()
            if self.ser.alive:
                self.port_disconnect = False
                msg = "Open [{0}] Successfully!".format(port_set["port_info"])
                font_color = "green"
            else:
                msg = "Something wrong with your serial port!"
                font_color = "red"
        except Exception as e:
            self.log.error(e)
            msg = "Open [{0}] Failed!".format(port_set["port_info"])
            font_color = "red"
        self.socketio.emit('port_status', {'msg': msg, 'color': font_color}, namespace='/power_cycle/test')

    def close_port(self):
        try:
            self.ser.stop()
            self.port_selected = None
            if not self.ser.alive:
                msg = "Ready"
                self.socketio.emit('port_status', {'msg': msg, 'color': "white"}, namespace='/power_cycle/test')
        except Exception as e:
            self.log.error(e)

    def send_msg(self, msg, is_hex):
        self.ser.write(msg.encode('utf-8'), isHex=is_hex)

    def power(self, status):
        with open(self.state_path) as f:
            status_running = json.load(f)
        if status_running["power_cycle_status"] == 0:
            self.print_log("You stopped running!!!", "red")
            self.socketio.emit("stop_confirm", namespace='/power_cycle/test')
            sys.exit()
        if status == "on":
            time_delay = float(self.ini["time_on"])
            if "-" in self.ini["button_press_on"]:
                val = self.ini["button_press_on"].split("-")
                button_press_delay = round(random.uniform(float(val[0]), float(val[1])), 4)
            else:
                button_press_delay = float(self.ini["button_press_on"])
            ac_address = 'B'
        else:
            time_delay = float(self.ini["time_off"])
            if "-" in self.ini["button_press_off"]:
                val = self.ini["button_press_off"].split("-")
                button_press_delay = round(random.uniform(float(val[0]), float(val[1])), 4)
            else:
                button_press_delay = float(self.ini["button_press_off"])
            ac_address = 'A'
        self.print_log('Powering {}...'.format(status))
        if not self.port_disconnect:
            try:
                if self.ini["relay_type"] == 'Button':
                    self.ser.write(self.ini["port_address"].encode('utf-8'), isHex=True)
                    self.print_log("button press delay = {}s".format(button_press_delay))
                    self.delay(button_press_delay)
                    self.ser.write("00".encode('utf-8'), isHex=True)
                else:
                    self.ser.write(ac_address.encode('utf-8'))
                self.print_log('Waiting {} seconds'.format(time_delay))
                self.delay(time_delay)
            except Exception as e:
                self.print_log('Error when powering on: {0}'.format(e), 'red')
                return False
        else:
            self.print_log('Serial Port seems disconnected......', 'red')
            return False
        return True

    def stop_confirm(self):
        self.socketio.emit('stop_confirm', {'data': "stopped"},
                           namespace='/power_cycle/test')

    def power_cycle(self, ini):
        self.ini = ini
        if self.ser.alive:
            if self.ini["relay_type"] == 'Button':
                self.delay(0.5)
                self.ser.write('50'.encode('utf-8'), isHex=True)
                self.delay(0.5)
                self.ser.write('51'.encode('utf-8'), isHex=True)
                self.delay(0.5)
                self.ser.write('00'.encode('utf-8'), isHex=True)

            for i in range(1, int(self.ini["total_count"]) + 1):
                self.print_log('This is >>>>>>>>>> %i<<<<<<<<<< times' % i)
                if not self.power('on'):
                    return False
                if not self.power('off'):
                    return False
            self.print_log('Power on your device...')
            self.power('on')
            self.print_log('-' * 37)
            self.print_log('*********Running over*********')
            self.print_log('-' * 37)
            self.delay(0.5)
        else:
            return False
        return True
