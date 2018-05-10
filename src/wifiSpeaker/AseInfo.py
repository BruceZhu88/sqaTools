"""
Created on Jan 3, 2017

@author: Bruce zhu
"""
import requests
import re
import json
import subprocess
import os
import datetime
# import socket
from threading import Thread, Lock
from time import sleep
from urllib import parse
# from urllib.error import URLError
from src.common.Logger import Logger
from src.common.SshHelper import SshHelper
from src.common.WindowsWifi import WindowsWifi
from src.common.Url import *
from src.wifiSpeaker.AseWebData import *
lock = Lock()


class AseInfo(object):
    def __init__(self):
        self.log = Logger("wifi_speaker").logger()
        self.ip = 'NA'
        self.device = 'NA'
        self.urlSetData = "http://{}/api/setData?{}"
        self.urlGetData = "http://{}/api/getData?{}"
        self.urlGetRows = "http://{}/api/getRows?{}"
        self.devices_list = []
        self.threads = []
        self.status = 0

    def transfer_data(self, request_way, ip, value, timeout=None):
        value_str = parse.urlencode(value, encoding="utf-8")
        if "+" in value_str:
            value_str = value_str.replace('+', '')
        if "True" in value_str:
            value_str = value_str.replace('True', 'true')
        if "False" in value_str:
            value_str = value_str.replace('False', 'false')
        if "%27" in value_str:
            value_str = value_str.replace('%27', '%22')
        if request_way == "get":
            url = self.urlGetData.format(ip, value_str, timeout=timeout)
            return request_url(url)
        elif request_way == "getRows":
            url = self.urlGetRows.format(ip, value_str, timeout=timeout)
            return request_url(url)
        elif request_way == "set":
            url = self.urlSetData.format(ip, value_str, timeout=timeout)
            return request_url(url)
        else:
            self.log.info("No such request method: {}".format(request_way))

    @staticmethod
    def ota_update(ip, ota_file):
        """
        ASE OTA Update
        :param ip: Device ip
        :param ota_file: Must be dict
        :return: Number type(post status)
        """
        url = "http://{}/page_setup_swupdate.fcgi?firmwareupdate=1".format(ip)
        req = requests.post(url=url, files=ota_file)
        return req.status_code

    def trigger_update(self, ip):
        return self.transfer_data("set", ip, update_para)["status"]

    def get_info(self, x, ip, timeout=None):
        try:
            if x == 'basicInfo':
                resp_value = request_url('http://{0}/index.fcgi'.format(ip))['text']
                data = re.findall('dataJSON = \'(.*)\';', resp_value)[0]
                resp_value = request_url('http://{0}/page_status.fcgi'.format(ip))['text']
                product_id = re.findall('var productId = \'(.*)\';', resp_value)[0]
                jd = json.loads(product_id, encoding='utf-8')
                sn = ''
                for i in jd["beoGphProductIdData"]["serialNumber"]:
                    sn = sn + str(i)
                data = json.loads(data, encoding='utf-8')
                info = {'modelName': data['beoMachine']['modelName'],
                        'model': data['beoMachine']['model'],
                        'productName': data['beoMachine']['setup']['productName'],
                        'bootloaderVersion': data['beoMachine']['fepVersions']['bootloaderVersion'],
                        'appVersion': data['beoMachine']['fepVersions']['appVersion'],
                        'sn': sn}
                return info
            if x == 'BeoDevice':
                r = request_url(beo_device.format(ip))['text']
                data = json.loads(r, encoding='utf-8')
                info = {'productType': data['beoDevice']['productId']['productType'],
                        'serialNumber': data['beoDevice']['productId']['serialNumber'],
                        'productFriendlyName': data['beoDevice']['productFriendlyName']['productFriendlyName'],
                        'version': data['beoDevice']['software']['version']}
                return info
            elif x == 'device_name':
                data = self.transfer_data("get", ip, deviceName_para, timeout=timeout)['text']
                device_name = json.loads(data, encoding='utf-8')[0]['string_']
                return device_name
            elif x == 'device_version':
                data = self.transfer_data("get", ip, displayVersion_para)['text']
                data = json.loads(data, encoding='utf-8')
                return data[0]["string_"]
            elif x == 'wifi_device':
                data = self.transfer_data("get", ip, WirelessSSID_para)['text']
                data = json.loads(data, encoding='utf-8')
                return data[0]["string_"]
            # elif x == 'wifi_level':
            #    data = self.transfer_data("get", ip, wifiSignalLevel_para)
            #    return re.findall(':\\[(.+)\\]}', data)[0]
            elif x == 'volume_default':
                data = self.transfer_data("get", ip, volumeDefault_para)['text']
                data = json.loads(data, encoding='utf-8')
                return data[0]["i32_"]
            elif x == 'volume_max':
                data = self.transfer_data("get", ip, volumeMax_para)['text']
                data = json.loads(data, encoding='utf-8')
                return data[0]["i32_"]
            elif x == 'bt_open':
                data = self.transfer_data("get", ip, pairingAlwaysEnabled_para)['text']
                data = json.loads(data, encoding='utf-8')
                return data[0]["bool_"]
            elif x == 'bt_reconnect':
                data = self.transfer_data("get", ip, autoConnect_para)['text']
                data = json.loads(data, encoding='utf-8')
                connect_mode = data[0]["bluetoothAutoConnectMode"]
                if connect_mode == 'manual':
                    return 'Manual'
                elif connect_mode == 'automatic':
                    return 'Automatic'
                else:
                    return 'Disable'
            elif x == 'bt':
                data = self.transfer_data("getRows", ip, pairedPlayers_para)['text']
                value = json.loads(data, encoding='GBK')  # Avoid chinese strings
                return value
            else:
                return 'NA'
        except Exception as e:
            self.log.debug('cmd = {0}, error: {1}'.format(x, e))
            return 'NA'

    def scan_wifi(self, ip):
        data = self.transfer_data("getRows", ip, network_scan_results_para)
        return data

    def pair_bt(self, pair, ip):
        if pair == 'pair':
            para = pairBT_para
        # elif pair == 'cancel':
        else:
            para = pairCancelBT_para
        self.transfer_data("set", ip, para)

    def reset(self, ip):
        self.transfer_data("set", ip, factoryResetRequest_para)

    def change_product_name(self, name, ip):
        self.transfer_data("set", ip, set_device_name(name))

    def log_submit(self, ip):
        values = self.transfer_data("set", ip, logReport_para)
        return values["status"]

    def log_clear(self, ip):
        values = self.transfer_data("set", ip, clearLogs_para)
        return values["status"]

    def bt_open_set(self, open_enable, ip):
        self.transfer_data("set", ip, set_pairing_mode(open_enable))

    def bt_remove(self, bt_mac, ip):
        bt_mac = bt_mac.replace(":", "_")
        self.transfer_data("set", ip, bt_remove_para(bt_mac))

    def bt_reconnect_set(self, status, ip):
        if status == 'Manual':
            mode = 'manual'
        elif status == 'Automatic':
            mode = 'automatic'
        elif status == 'Disable':
            mode = 'none'
        else:
            return
        self.transfer_data("set", ip, set_bt_mode(mode))

    @staticmethod
    def get_current_source(ip):
        url = current_source.format(ip)
        r = request_url(url)['text']
        data = json.loads(r, encoding='utf-8')
        if len(data) == 0:
            return 'Standby'
        else:
            return data['friendlyName']
    """
    def status_dynamic(self, x, ip):
        device_volume_url = 'http://' + ip + '/api/getData?path=BeoSound%3A%2Fvolume&roles=value&'
        device_battery = 'http://' + ip + '/api/getData?path=power%3AenergyState&roles=value&'
        try:
            if x == 'volume_current':
                return re.findall('i32_":(.+),', request_url(device_volume_url))[0]
            if x == 'batteryPercentage':
                return re.findall('batteryPercentage":(\\d+),', request_url(device_battery))[0]
            if x == 'batteryHealthStatus':
                return re.findall('batteryHealthStatus":"(.+)","batteryStatus', request_url(device_battery))[
                    0]
            if x == 'batteryStatus':
                return re.findall('batteryStatus":"(.+)","timestamp', request_url(device_battery))[0]
            return 'NA'
        except:
            return 'NA'
    """
    # ==================================================================================================================

    def setup_wifi(self, ssid="", key="", dhcp=True, ip="", gateway="", netmask="", originalIp=""):
        # logging.log(logging.INFO, "Setup wifi ssid=%s key=%s"%(wifissid,pwd))
        encryption = "wpa_psk"
        if key == "":
            encryption = "none"
        wireless = {"dhcp": dhcp,
                    "dns": ["", ""],
                    "gateway": gateway,
                    "encryption": encryption,
                    "ip": ip,
                    "ssid": ssid,
                    "netmask": netmask,
                    "key": key}
        wired = {"dhcp": dhcp,
                 "dns": ["", ""],
                 "gateway": "",
                 "ip": "",
                 "netmask": ""}
        network_profile = {"wireless": wireless,
                           "wired": wired,
                           "type": "automatic", }
        value = {"networkProfile": network_profile,
                 "type": "networkProfile", }
        wifi_value = {"path": "BeoWeb:/network", "roles": "activate",
                      "value": value}
        try:
            self.transfer_data("set", originalIp, wifi_value)
        except Exception as e:
            self.log.info(e)
            return False
        else:
            return True

    # ==================================================================================================================
    @staticmethod
    def get_ase(ip, info):
        """For unblock device"""
        # info = 'readinfo'
        cmd = r'"{}\\config\\thrift\\thrift2.exe"'.format(os.getcwd()) + " {} 1 {}".format(ip, info)
        s = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        pipe = s.stdout.readlines()
        return pipe

    def unblock_device(self, ip):
        self.log.debug('Start unblock...')
        try:
            status = str(self.get_ase(ip, 'readinfo')[-1], 'utf-8')
        except Exception as e:
            self.log.error(e)
            return False
        if 'Successful' in status:
            self.log.debug('Unblock successfully!')
            return True
        self.log.debug('Unblock failed!')
        return False

    # ==================================================================================================================
    def get_ase_devices_list(self):
        # self.devices_list.clear()
        self.devices_list = []
        self.status = 0
        get_ip = WindowsWifi().discover_ips()
        self.log.debug(get_ip)
        self.threads = []
        for ip in get_ip:
            t = Thread(target=self.scan_devices, args=(ip,))
            t.setDaemon(True)
            t.start()
            self.threads.append(t)
            sleep(0.005)    # avoid network block
        thread_status = Thread(target=self.scan_status, args=())
        thread_status.setDaemon(True)
        thread_status.start()

    def scan_devices(self, ip):
        response = request_url(beo_device.format(ip), timeout=6)
        # if not self.check_url_status("http://{}/index.fcgi".format(ip), timeout=6):  # timeout need modify
        if response['status'] != 200:
            return
        data = json.loads(response['text'], encoding='utf-8')
        device_name = data['beoDevice']['productFriendlyName']['productFriendlyName']
        model_name = data['beoDevice']['productId']['productType']
        # device_name = self.get_info("device_name", ip)
        # model_name = self.get_info("basicInfo", ip)['modelName']
        try:
            """
            result = socket.gethostbyaddr(ip)
            try:
                host_name = result[0].replace(".lan", "")
            except Exception as e:
                self.log.error("host name not contain .lan" + e)
                return
            """
            if lock.acquire():
                self.devices_list.append("{} ({}) [{}]".format(device_name, ip, model_name))
                # self.devices_list.append("{} ({})".format(host_name, ip))
                lock.release()
        # except socket.herror as e:
        except Exception as e:
            pass
            # self.log.debug("Couldn't look up name: " + ip + str(e))

    def scan_status(self):
        for td in self.threads:
            td.join()
        self.status = 1

    def return_devices(self):
        return {"status": self.status, "devices": self.devices_list}
    # ==================================================================================================================

    def send_cmd(self, ip, cmd):
        user = 'root'
        ssh_rsa = './data/ssh-rsa'
        ssh_path = '{}/config/OpenSSH/'.format(os.getcwd())
        ssh = SshHelper(ip, user, ssh_rsa, ssh_path)
        content = ssh.execute(cmd)
        if len(content) == 0:
            if self.unblock_device(ip):
                content = ssh.execute(cmd)
            else:
                self.log.error('Cannot communicate with your sample!')
        return content

    def get_log_files(self, ip, sn, cmd, save_path):
        save_path = os.path.abspath(save_path)
        if not os.path.exists(save_path):
            os.mkdir(save_path)
        path = os.path.join(save_path, '{}_{}_{}.log'.format(
            cmd.rsplit('/', 1)[1], sn, datetime.datetime.now().strftime('%m%d_%H_%M_%S')))
        try:
            content = self.send_cmd(ip, cmd)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            self.log.error(e)
            path = ""
        return path

    def download_log(self, ip, sn, script_path, save_path):
        path, content = '', ''
        with open(script_path, 'r') as f:
            for l in f.readlines():
                cmd = l.replace('\n', '')
                content = self.send_cmd(ip, cmd)
            url = re.findall(r'http:.*tgz', content)
            if len(url) > 0:
                path = os.path.join(os.path.abspath(save_path), 'log_{}.tgz'.format(sn))
                try:
                    request.urlretrieve(url[0], path)
                except Exception as e:
                    self.log.error(e)
                    path = ''
        return path


if __name__ == "__main__":
    ase_info = AseInfo()
    files = {
        'file': open(r'‪D:\bruce\Tymphany\Test_case\CA17\version\ase2ca17s810-release-1-0-15059-28653020', 'rb')
    }
    ase_info.ota_update("192.168.1.160", files)
