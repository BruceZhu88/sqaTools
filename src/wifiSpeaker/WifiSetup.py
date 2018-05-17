# coding = utf-8
# Author: Bruce.Zhu

import re
import sys
import urllib.request
from time import sleep
from src.common.Logger import Logger
from src.common.WindowsWifi import WindowsWifi
from src.wifiSpeaker.AseInfo import AseInfo


class WifiSetup(object):
    def __init__(self, ip, product_name, wifi_setting, socketio):
        self.socketio = socketio
        self.wifi_ini = wifi_setting
        self.log = Logger("wifi_speaker").logger()
        self.wifi = WindowsWifi(socketio=socketio)
        self.ase_info = AseInfo()
        self.total_times = 0
        self.success_times = 0
        self.ip = ip
        self.product_name = product_name

    def print_log(self, info, color='white'):
        try:
            self.log.info(info)
            if self.socketio is not None:
                self.socketio.sleep(0.01)  # Avoid sockeit network block leads to cannot print on page
                self.socketio.emit('print_msg',
                                   {'data': info, 'color': color},
                                   namespace='/wifi_speaker/test')
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

    def reset_and_wait(self, ip, t):
        self.ase_info.reset(ip)
        self.print_log("Doing factory reset. Waiting %ss..." % t)
        self.delay(t)

    def check_wifi_status(self, ip):
        try:
            response = urllib.request.urlopen(ip, timeout=20)
            status = response.status
            if status == 200:
                return True
            else:
                return False
        except Exception as e:
            self.print_log("Cannot connect {}: {}".format(ip, e))
            return False

    def setup(self):
        try:
            self.wifi_ini.cfg_load()
            times = self.wifi_ini.cfg.getint("Run", "total_times")
            time_reset = self.wifi_ini.cfg.getint("Run", "time_reset")
            dhcp = self.wifi_ini.cfg.get("Wifi", "dhcp")
            ssid = self.wifi_ini.cfg.get("Wifi", "ssid")
            key = self.wifi_ini.cfg.get("Wifi", "password")
            # encryption = wifi_setting.cfg.get("Wifi", "encryption")
            ip = self.wifi_ini.cfg.get("Wifi", "static_ip")
            gateway = self.wifi_ini.cfg.get("Wifi", "gateway")
            netmask = self.wifi_ini.cfg.get("Wifi", "netmask")
            self.wifi_ini.save()
        except Exception as e:
            self.log.error(e)
            sys.exit()
        # hostName = "beoplay-{model}-{SN}.local".format(model=model, SN=SN)
        host_url = "http://{}/index.fcgi"

        DHCP = []
        if dhcp == "True" or dhcp == "true":
            DHCP.append(True)
        elif dhcp == "False" or dhcp == "false":
            DHCP.append(False)
        else:
            DHCP.extend([True, False, True])
        self.total_times = times

        for cycle in range(1, times + 1):
            self.print_log("This is the %d times " % cycle)
            for index in DHCP:
                dhcp = index
                static_ip, static_gateway, static_netmask= '', '', ''
                if not dhcp:
                    static_ip, static_gateway, static_netmask = ip, gateway, netmask
                self.print_log("Set DHCP={}".format(dhcp))
                self.reset_and_wait(self.ip, time_reset)
                while True:
                    if self.wifi.find_wifi(self.product_name):
                        self.wifi.connect_wifi(self.product_name)
                        self.delay(15)  # Give wifi connect some time
                        if self.wifi.check_wifi(self.product_name):
                            break
                    self.delay(3)

                if not self.check_wifi_status("http://192.168.1.1/index.fcgi#Fts/Network"):
                    return
                if self.ase_info.setup_wifi(ssid, key, dhcp, static_ip, static_gateway, static_netmask, "192.168.1.1"):
                    self.print_log("Wifi setup command has been sent!")
                    if self.wifi.find_wifi(ssid):
                        self.wifi.connect_wifi(ssid)
                        self.delay(15)  # Give wifi connect some time
                        if self.wifi.check_wifi(ssid):
                            scan_result = 0
                            for i in range(0, 10):
                                if scan_result == 1:
                                    break
                                devices = self.scan_devices()
                                for d in devices:
                                    if self.product_name in d:
                                        scan_result = 1
                                        self.ip = re.findall('\((.*)\)', d)[0]
                                        break
                            if scan_result == 0:
                                self.print_log("Something wrong when scan devices!")
                                sys.exit()
                            if self.check_wifi_status(host_url.format(self.ip)):
                                if not dhcp:
                                    if ip == self.ip:
                                        self.print_log("Your static ip[{}] setup successfully!".format(ip))
                                    else:
                                        self.print_log("Your static ip[{}] setup Failed!".format(ip))
                                        return
                                else:
                                    self.print_log("Wifi[{}] setup successfully!".format(ssid))
                                self.success_times = self.success_times + 1
                        else:
                            self.print_log("Cannot connect wifi %s" % ssid)
                            break
                self.socketio.emit("wifi_setup_pass_ratio", {"data": "{}/{}".format(self.success_times, cycle)}
                                   , namespace="/wifi_speaker/test")

            if self.success_times >= self.total_times:
                finish_print = "**********All finished*********"
                self.print_log(finish_print)

    def scan_devices(self):
        self.print_log("Scanning devices")
        self.ase_info.get_ase_devices_list()
        while True:
            devices_list = self.ase_info.return_devices()
            status = devices_list.get("status")
            if status == 1:
                return devices_list.get("devices")
