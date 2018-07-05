
import time
import random
from .SerialHelper import SerialHelper


class Relay(object):
    def __init__(self, log):
        self.log = log
        self.ser = None

    def init_relay(self, port):
        """Before operating relay, you must initialize it first.
        """
        self.ser = SerialHelper()
        self.ser.port = port
        self.ser.start()

    def stop_relay(self):
        self.ser.stop()

    def init_button(self):
        if self.ser.alive:
            try:
                time.sleep(0.5)
                self.ser.write('50'.encode('utf-8'), isHex=True)
                time.sleep(0.5)
                self.ser.write('51'.encode('utf-8'), isHex=True)
                time.sleep(0.5)
                self.ser.write('00'.encode('utf-8'), isHex=True)
                return True
            except Exception as e:
                self.log.info(e)
        return False

    def press(self, key: list, t):
        """Press and release relay port
        :param key: list type,
                    That means you also could control many ports simultaneously, key = '01', '02'
        :param t: string type, the time of press
        :return None
        """
        if not self.ser.alive:
            return
        k = '00'
        for v in key:
            k = hex(int(v, 16) ^ int(k, 16))
        if len(k) == 3:
            k = k.replace('0x', '0x0')
        if "-" in t:
            val = t.split("-")
            delay = round(random.uniform(float(val[0]), float(val[1])), 4)
        else:
            delay = float(t)
        k = k.replace('0x', '')
        # close relay
        self.ser.write(k.encode('utf-8'), isHex=True)
        # How long do you need to press
        self.log.info('button press time={}'.format(delay))
        time.sleep(delay)
        # release relay
        self.ser.write('00'.encode('utf-8'), isHex=True)

    def ac_power(self, state):
        if not self.ser.alive:
            return False
        try:
            if state.lower() == 'on':
                self.ser.write('B'.encode('utf-8'))
            else:
                self.ser.write('A'.encode('utf-8'))
        except Exception as e:
            self.log.error(e)
            return False
        return True
