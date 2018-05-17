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
        self.INFO = {}

    def transfer_data(self, request_way, ip, value, timeout=None):
        """
        :param request_way:
        :param ip:
        :param value:
        :param timeout:
        :return:
        %27 = ', %22 = ", + = 'space'
        """
        value_str = parse.urlencode(value, encoding="utf-8")
        if "+" in value_str:
            value_str = value_str.replace('+', '')
        if "True" in value_str:
            value_str = value_str.replace('True', 'true')
        if "False" in value_str:
            value_str = value_str.replace('False', 'false')
        if "%27" in value_str:
            value_str = value_str.replace('%27', '%22')
        if white_space in value_str:
            value_str = value_str.replace(white_space, '+')
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
                r = request_url('http://{0}/index.fcgi'.format(ip))
                if r.get('status') != 200:
                    return 'error'
                text = re.findall('dataJSON = \'(.*)\';', r.get('text'))[0]
                data = json.loads(text, encoding='utf-8')
                '''
                r = request_url('http://{0}/page_status.fcgi'.format(ip))['text']
                product_id = re.findall('var productId = \'(.*)\';', r)[0]
                jd = json.loads(product_id, encoding='utf-8')
                sn = ''
                for i in jd["beoGphProductIdData"]["serialNumber"]:
                    sn = sn + str(i)
                '''
                beo_machine = data.get('beoMachine')
                fep_versions = beo_machine.get('fepVersions')
                info = {'modelName': beo_machine.get('modelName'),
                        'model': beo_machine.get('model'),
                        'productName': beo_machine.get('setup').get('productName'),
                        'bootloaderVersion': fep_versions.get('bootloaderVersion'),
                        'appVersion': fep_versions.get('appVersion')
                        }
                self.INFO['appVersion'] = info['appVersion']
                return info
            elif x == 'BeoDevice':
                r = request_url(beo_device.format(ip))
                if r.get('status') != 200:
                    return 'error'
                data = json.loads(r.get('text'), encoding='utf-8')
                beo_info = data.get('beoDevice')
                beo_productid = beo_info.get('productId')
                info = {'productType': beo_productid.get('productType'),
                        'serialNumber': beo_productid.get('serialNumber'),
                        'productFriendlyName': beo_info.get('productFriendlyName').get('productFriendlyName'),
                        'version': beo_info.get('software').get('version')
                        }
                self.INFO["sn"] = info['serialNumber']
                self.INFO["deviceName"] = info['productFriendlyName']
                self.INFO["version"] = info['version']
                return info
            elif x == 'bluetoothSettings':
                r = request_url(bluetooth_settings.format(ip))
                if r.get('status') != 200:
                    return 'error'
                data = json.loads(r.get('text'), encoding='utf-8')
                bluetooth = data.get('profile').get('bluetooth')
                device_settings = bluetooth.get('deviceSettings')
                always_open = device_settings.get('alwaysOpen')
                reconnect_mode = device_settings.get('reconnectMode')
                devices = bluetooth.get('devices')
                bt_devices = devices.get('device')
                info = {'bt_open': always_open,
                        'bt_reconnect_mode': reconnect_mode,
                        'bt_devices': bt_devices}
                self.INFO['bluetoothSettings'] = info
                return info
            elif x == 'device_name':
                data = self.transfer_data("get", ip, deviceName_para, timeout=timeout)['text']
                device_name = json.loads(data, encoding='utf-8')[0]['string_']
                return device_name
            elif x == 'device_version':
                data = self.transfer_data("get", ip, displayVersion_para)['text']
                data = json.loads(data, encoding='utf-8')
                return data[0].get("string_")
            elif x == 'wifi_device':
                data = self.transfer_data("get", ip, WirelessSSID_para)['text']
                data = json.loads(data, encoding='utf-8')
                return data[0].get("string_")
            # elif x == 'wifi_level':
            #    data = self.transfer_data("get", ip, wifiSignalLevel_para)
            #    return re.findall(':\\[(.+)\\]}', data)[0]
            elif x == 'volume_default':
                data = self.transfer_data("get", ip, volumeDefault_para)['text']
                data = json.loads(data, encoding='utf-8')
                return data[0].get("i32_")
            elif x == 'volume_max':
                data = self.transfer_data("get", ip, volumeMax_para)['text']
                data = json.loads(data, encoding='utf-8')
                return data[0].get("i32_")
            elif x == 'bt_open':
                data = self.transfer_data("get", ip, pairingAlwaysEnabled_para)['text']
                data = json.loads(data, encoding='utf-8')
                value = data[0].get("bool_")
                self.INFO['bt_open'] = value
                return value
            elif x == 'bt_reconnect':
                data = self.transfer_data("get", ip, autoConnect_para)['text']
                data = json.loads(data, encoding='utf-8')
                connect_mode = data[0].get("bluetoothAutoConnectMode")
                if connect_mode == 'manual':
                    mode = 'Manual'
                elif connect_mode == 'automatic':
                    mode = 'Automatic'
                else:
                    mode = 'Disable'
                self.INFO['bt_reconnect'] = mode
                return mode
            elif x == 'bt':
                data = self.transfer_data("getRows", ip, pairedPlayers_para)['text']
                value = json.loads(data, encoding='GBK')  # Avoid chinese strings
                self.INFO['bt_devices'] = value
                return value
            elif x == 'network_settings':
                r = request_url(network_settings.format(ip))
                if r.get('status') != 200:
                    return 'error'
                data = json.loads(r.get('text'), encoding='utf-8')
                network_info = data.get('profile').get('networkSettings')
                interfaces = network_info.get('interfaces')
                active_interface = network_info.get('activeInterface')
                # wired = interfaces.get('wired')
                wireless = interfaces.get('wireless')
                active_network = wireless.get('activeNetwork')
                internet_reachable = 'Yes' if network_info.get('internetReachable') else 'No'
                dhcp = 'Yes' if active_network.get('dhcp') else 'No'
                if active_interface == 'wireless':
                    info = {
                        'Active Interface': 'Wi-Fi',
                        'Internet Reachable': internet_reachable,
                        'SSID': active_network.get('ssid'),
                        'DHCP': dhcp,
                        'Frequency': active_network.get('frequency').replace('ghz', ' GHz'),
                        'Quality': active_network.get('quality'),
                        'RSSI': active_network.get('rssi'),
                        'Encryption': active_network.get('encryption').replace('Psk', '-PSK').replace(
                            'Tkip', '(TKIP)').upper()
                    }
                else:
                    info = {
                        'Active Interface': 'Ethernet',
                        'Internet Reachable': internet_reachable,
                        'Wifi configured': 'Yes' if active_network.get('configured') else 'No',
                        'DHCP': dhcp
                    }
                self.INFO['network_settings'] = info
                return info
            elif x == 'current_source':
                r = request_url(current_source.format(ip))
                if r.get('status') != 200:
                    return 'error'
                data = json.loads(r.get('text'), encoding='utf-8')
                if len(data) == 0:
                    source = 'None'
                else:
                    source = data.get('friendlyName')
                self.INFO['current_source'] = source
                return source
            elif x == 'get_standby':
                r = request_url(standby_status.format(ip))
                if r.get('status') != 200:
                    return 'error'
                data = json.loads(r.get('text'), encoding='utf-8')
                status = data.get('standby').get('powerState')
                status = status.replace(status[0], status[0].upper())
                self.INFO['standby_status'] = status
                return status
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
        return self.transfer_data("set", ip, para)['status']

    def reset(self, ip):
        return self.transfer_data("set", ip, factoryResetRequest_para)['status']

    def change_product_name(self, name, ip):
        return self.transfer_data("set", ip, set_device_name(name))['status']

    def log_submit(self, ip):
        return self.transfer_data("set", ip, logReport_para)["status"]

    def log_clear(self, ip):
        return self.transfer_data("set", ip, clearLogs_para)['status']

    def bt_open_set(self, open_enable, ip):
        return self.transfer_data("set", ip, set_pairing_mode(open_enable))['status']

    def bt_remove(self, bt_mac, ip):
        bt_mac = bt_mac.replace(":", "_")
        return self.transfer_data("set", ip, bt_remove_para(bt_mac))['status']

    def bt_reconnect_set(self, mode, ip):
        if mode == 'disabled':
            mode = 'none'
        return self.transfer_data("set", ip, set_bt_mode(mode))['status']

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
        wifi_value = wifi_settings(ssid, key, encryption, dhcp, ip, gateway, netmask)
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
        response = request_url(beo_device.format(ip), timeout=5)
        # if not self.check_url_status("http://{}/index.fcgi".format(ip), timeout=6):  # timeout need modify
        if response['status'] != 200:
            return
        data = json.loads(response['text'], encoding='utf-8')
        beo_info = data.get('beoDevice')
        device_name = beo_info.get('productFriendlyName').get('productFriendlyName')
        model_name = beo_info.get('productId').get('productType')
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

    def thread_get_info(self, ip):
        if not check_url_status(beo_device.format(ip), timeout=5):
            return False
        # self.devices_list.clear()
        # basic_info = ase_info.get_info("basicInfo", ip)
        # beo_device_info = ase_info.get_info('BeoDevice', ip)
        self.INFO["ip"] = ip
        info = ['BeoDevice', 'basicInfo', 'bluetoothSettings', 'current_source', 'get_standby']
        # threads = []
        for i in info:
            self.get_info(i, ip)
        '''
            t = Thread(target=self.get_info, args=(i, ip))
            t.setDaemon(True)
            t.start()
            threads.append(t)
            # sleep(0.02)    # avoid network block
        for td in threads:
            td.join()
        '''
        self.INFO["device_versions"] = '{} ({} / {})'.format(
            self.INFO.get('version'), self.INFO.get('appVersion'), self.INFO.get('sn'))
        return self.INFO

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
        save_path = os.path.abspath(save_path)
        if not os.path.exists(save_path):
            os.mkdir(save_path)
        path, content = '', ''
        with open(script_path, 'r') as f:
            for l in f.readlines():
                cmd = l.replace('\n', '')
                content = self.send_cmd(ip, cmd)
            url = re.findall(r'http:.*tgz', content)
            if len(url) > 0:
                path = os.path.join(save_path, 'log_{}.tgz'.format(sn))
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
