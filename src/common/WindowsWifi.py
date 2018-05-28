# coding=utf-8
#
# Author: Bruce Zhu
#
# import netifaces   ---> some os cannot loads this dll(is not a valid win32 application)
import os
import re
import sys
import subprocess
import socket
from time import sleep
from ctypes import windll
from src.common.Logger import Logger
logger = Logger("wifi_speaker").logger()


class WindowsWifi(object):
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.log = Logger("wifi_speaker").logger()
        # *************************************************************
        # Chinese: 0x804
        # English: 0x409
        dll_handle = windll.kernel32
        id = hex(dll_handle.GetSystemDefaultUILanguage())
        if id == "0x804":
            system_language = "Chinese"
        elif id == "0x409":
            system_language = "English"
        else:
            system_language = ""
        self.log.debug("system language: "+system_language)
        # *************************************************************
        p = subprocess.Popen("chcp", shell=True, stdout=subprocess.PIPE)
        try:
            code = p.stdout.read().decode("GB2312")
        except:
            code = p.stdout.read().decode("utf-8")
        # if system_language == "Chinese":
        if self.contain_zh(code) is not None:
            self.wifi_state = "已连接"
            self.wifi_state_find = "状态"
            self.ipType = "动态"
        else:
            self.wifi_state = "connected"
            self.wifi_state_find = "State"
            self.ipType = "dynamic"

    def print_log(self, info):
        try:
            self.log.info(info)
            if self.socketio is not None:
                self.socketio.sleep(0.01)
                self.socketio.emit('print_msg',
                                   {'data': info},
                                   namespace='/test')
            else:
                print(info)
        except Exception as e:
            self.log.debug("Error when print_log: {}".format(e))
            sys.exit()

    def delay(self, t):
        if self.socketio is not None:
            self.socketio.sleep(t)
        else:
            sleep(t)

    @staticmethod
    def contain_zh(word):
        """:return None: no"""
        zh_pattern = re.compile(u'[\u4e00-\u9fa5]+')
        match = zh_pattern.search(word)
        return match

    def connect_wifi(self, name):
        self.print_log("Try to connect wifi --> %s" % name)
        p = os.popen("netsh wlan connect name=\"{name}\"".format(name=name))
        content = p.read()
        self.print_log(content)
        # os.system("netsh wlan connect name=%s" % name)

    def wifi_status(self):
        self.print_log("Checking wifi status...")
        p = os.popen("netsh wlan show interfaces")
        content = p.read()
        return content

    def check_wifi(self, wifi_name):
        # self.print_log(content)
        for i in range(0, 5):
            content = self.wifi_status()
            try:
                wifi_ssid = re.findall(u"SSID(.*)", content)[0].split(": ")[1]
                wifi_state = re.findall(u"%s(.*)" % self.wifi_state_find, content)[0].split(": ")[1]
                # self.print_log(wifi_state)
                if wifi_ssid == wifi_name:
                    if wifi_state == self.wifi_state:
                        self.print_log("Wifi %s connected!" % wifi_name)
                        return True
                self.print_log("Wifi [%s] did not connected!" % wifi_name)
            except Exception as e:
                self.log.error("Check wifi:{}".format(e))
            self.delay(1)
        return False

    def find_wifi(self, str):
        self.print_log("Finding wifi %s  ..." % str)
        p = subprocess.Popen("netsh wlan disconnect",
                             shell=True)  # win10 system cannot auto refresh wifi list, so disconnect it first
        p.wait()
        # p = os.popen("netsh wlan show networks") #netsh wlan show networks mode=bssid
        # content = p.read().decode("gbk", "ignore")
        p = subprocess.Popen("netsh wlan show networks | find \"%s\"" % str, shell=True, stdout=subprocess.PIPE)
        try:
            content = p.stdout.read().decode("GB2312")  # byte decode to str, and GB2312 is avoid Chinese strings.
        except:
            content = p.stdout.read().decode("utf-8")
        if content != "":
            self.print_log("Find [%s]" % str)
            return True
        else:
            return False

    """
    @staticmethod
    def get_network_status():
        network_status = {}
        network_status['gateway'] = netifaces.gateways()['default'][netifaces.AF_INET][0]
        network_status['nicName'] = netifaces.gateways()['default'][netifaces.AF_INET][1]

        for interface in netifaces.interfaces():
            if interface == network_status['nicName']:
                network_status['mac'] = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
                try:
                    network_status['ip'] = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
                    network_status['netMask'] = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['netmask']
                except KeyError as e:
                    self.log.debug(e)
        return network_status
    """

    def discover_ips(self):
        """
        gateway = self.get_network_status()['gateway']
        ip = self.get_network_status()['ip']
        netmask = self.get_network_status()['netMask']
        # count_bit = lambda count_str: len([i for i in count_str if i == '1'])
        # count_bit("111111")
        netmask_bit = 0
        for n in netmask.split('.'):
            netmask_bit = netmask_bit + bin(int(n)).count('1')
        """
        ip = socket.gethostbyname(socket.gethostname())
        tmp = ip.rsplit(".", 1)[0]
        gateway = "{}.1".format(tmp)
        # netmask_bit = 24
        # path = "{}\config\\NBTscan-Ipanto.exe".format(os.getcwd())
        # cmd = r"{} {}/{}".format(path, gateway, netmask_bit)
        # self.log.debug(cmd)
        text = ""
        try:
            p = subprocess.Popen('net view', shell=True, stdout=subprocess.PIPE)
            p.wait()
            sleep(0.1)
            p = subprocess.Popen("arp -a", shell=True, stdout=subprocess.PIPE)
            text = p.stdout.readlines()
        except Exception as e:
            self.log.debug(e)
        ip_address = []
        for t in text:
            try:
                content = t.decode("GB2312")
            except:
                content = t.decode("utf-8")
            if self.ipType in content:
                # re.findall(r'(?:(?:[0,1]?\d?\d|2[0-4]\d|25[0-5])\.){3}(?:[0,1]?\d?\d|2[0-4]\d|25[0-5])')
                ip_filter = re.findall(r'\d+\.\d+\.\d+\.\d+', content)
                if len(ip_filter) != 0:
                    if gateway != ip_filter[0] and ip != ip_filter[0]:
                        ip_address.append(ip_filter[0])
        return {'ip': ip_address, 'gateway': gateway}


if __name__ == "__main__":
    wifi = WindowsWifi()
    # data = wifi.find_wifi("Beoplay M3_00094760")
    # print(data)
    print(wifi.discover_ips())
