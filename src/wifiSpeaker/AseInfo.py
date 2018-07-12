"""
Created on Jan 3, 2017

@author: Bruce zhu
"""
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
from src.common.util import store
from src.common.util import load
from src.common.cfg import Config
from src.common.Url import *
from src.wifiSpeaker.AseWebData import *
lock = Lock()

main_cfg_path = './config/main.conf'
main_config = Config(main_cfg_path)
main_config.cfg_load()
main_cfg = main_config.cfg

saved_ip_path = main_cfg.get('WifiSpeaker', 'saved_ip')


class AseInfo(object):
    def __init__(self):
        self.log = Logger("wifi_speaker").logger()
        self.ip = 'NA'
        self.device = 'NA'
        self.urlSetData = "http://{}/api/setData?{}"
        self.urlGetData = "http://{}/api/getData?{}"
        self.urlGetRows = "http://{}/api/getRows?{}"
        self.devices_list = []
        self.status = 0
        self.threads = []
        self.INFO = {}
        self.saved_ip = []

    def transfer_data(self, request_way, ip, value, timeout=6):
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
            url = self.urlGetData.format(ip, value_str)
        elif request_way == "getRows":
            url = self.urlGetRows.format(ip, value_str)
        elif request_way == "set":
            url = self.urlSetData.format(ip, value_str)
        else:
            self.log.error("No such request method: {}".format(request_way))
            return
        return requests_url(url, 'get', timeout=timeout)

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

    def get_info(self, x, ip):
        try:
            if x == 'basicInfo':
                r = request_url('http://{0}/index.fcgi'.format(ip), timeout=5)
                if r.get('status') != 200:
                    return 'error'
                text = re.findall('dataJSON = \'(.*)\';', r.get('content'))[0]
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
                r = request_url(beo_device.format(ip), timeout=5)
                if r.get('status') != 200:
                    return 'error'
                data = json.loads(r.get('content'), encoding='utf-8')
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
            elif x == 'modulesInformation':
                r = request_url(modules_info.format(ip), timeout=5)
                if r.get('status') != 200:
                    return 'error'
                data = json.loads(r.get('content'), encoding='utf-8')
                module = data.get('profile').get('module')
                info = {
                    'fep_application': module[0].get('application').get('version'),
                    'fep_bootloader': module[0].get('bootloader').get('version'),
                    # 'AP': module[2].get('application').get('version'),
                    # 'GoogleCast': module[3].get('application').get('version')
                }
                self.INFO['fep_app'] = info.get('fep_application')
                self.INFO['bootloader'] = info.get('fep_bootloader')
                return info
            elif x == 'bluetoothSettings':
                r = request_url(bluetooth_settings.format(ip), timeout=5)
                if r.get('status') != 200:
                    return 'error'
                data = json.loads(r.get('content'), encoding='utf-8')  # GBK? Chinese string
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
            elif x == 'network_settings':
                r = request_url(network_settings.format(ip), timeout=8)
                if r.get('status') != 200:
                    return 'error'
                data = json.loads(r.get('content'), encoding='utf-8')
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
            elif x == 'volume':
                r = requests_url(volume_speaker.format(ip), 'get')
                if r.get('status') != 200:
                    return 'error'
                data = json.loads(r.get('content'), encoding='utf-8')
                speaker = data.get('speaker')
                volume_range = speaker.get('range')
                speaker_volume = {
                    'Current Level': speaker.get('level'),
                    'Default Level': speaker.get('defaultLevel'),
                    'Muted': 'Yes' if speaker.get('muted') else 'No',
                    'Min': volume_range.get('minimum'),
                    'Max': volume_range.get('maximum')
                }
                self.INFO['speaker_volume'] = speaker_volume
                return speaker_volume
            elif x == 'current_source':
                r = request_url(current_source.format(ip), timeout=5)
                if r.get('status') != 200:
                    self.INFO['current_source'] = 'error'
                    return 'error'
                data = json.loads(r.get('content'), encoding='utf-8')
                if len(data) == 0:
                    source = 'None'
                else:
                    source = data.get('friendlyName')
                self.INFO['current_source'] = source
                return source
            elif x == 'get_standby':
                r = request_url(standby_status.format(ip), timeout=5)
                if r.get('status') != 200:
                    self.INFO['standby_status'] = 'error'
                    return 'error'
                data = json.loads(r.get('content'), encoding='utf-8')
                status = data.get('standby').get('powerState')
                status = status.replace(status[0], status[0].upper())
                self.INFO['standby_status'] = status
                return status
            elif x == 'regional_settings':
                r = request_url(regional_settings.format(ip), timeout=5)
                if r.get('status') != 200:
                    return 'error'
                data = json.loads(r.get('content'), encoding='utf-8')
                data_region = data.get('profile').get('regionalSettings')
                info = {
                    'Country': data_region.get('country').get('country'),
                    'Date Time': data_region.get('dateTime').get('dateTime'),
                    'Time Zone': data_region.get('timeZone').get('inTimeZone')
                }
                return info
            elif x == 'power_management':
                r = request_url(power_management.format(ip), timeout=5)
                if r.get('status') != 200:
                    return 'error'
                data = json.loads(r.get('content'), encoding='utf-8')
                data_power = data.get('profile').get('powerManagement')
                info = {
                    'Idle Timeout': data_power.get('idleTimeout').get('timeout'),
                    'Play Timeout': data_power.get('playTimeout').get('timeout')
                }
                return info
            elif x == 'muted':
                r = request_url(volume_speaker.format(ip) + '/Muted', timeout=5)
                if r.get('status') != 200:
                    self.INFO['muted'] = 'error'
                    return 'error'
                data = json.loads(r.get('content'), encoding='utf-8')
                muted = data.get('muted')
                self.INFO['muted'] = muted
                return muted
            elif x == 'stream_state':
                r = request_url(sys_products.format(ip), timeout=5)
                if r.get('status') != 200:
                    return 'error'
                data = json.loads(r.get('content'), encoding='utf-8')
                products = data.get('products')
                for k, v in enumerate(products):
                    name = self.get_info('BeoDevice', ip).get('productFriendlyName')
                    if v.get('friendlyName') == name:
                        state = v.get('primaryExperience').get('state')
                        source_type = v.get('primaryExperience').get('source').get('sourceType').get('type')
                        break
                info = {
                    'state': state,
                    'source_type': source_type
                }
                return info
            elif x == 'get_product_status':
                return self.get_product_status(ip)
            else:
                return 'NA'
        except Exception as e:
            self.log.debug('cmd = {0}, error: {1}'.format(x, e))
            return 'NA'

    def get_other_info(self, ip):
        li = ['power_management', 'regional_settings']
        title = {
            'power_management': 'Power Management',
            'regional_settings': 'Regional Settings'
        }
        info = {}
        for i in li:
            tmp = self.get_info(i, ip)
            if tmp == 'NA' or tmp == 'error':
                return {'error': 'error'}
            info[title[i]] = tmp
        return info

    @staticmethod
    def standby(ip):
        url = power_management.format(ip) + '/standby'
        payload = json.dumps({"standby": {"powerState": "standby"}})
        return requests_url(url, 'put', data=payload).get('status')

    @staticmethod
    def set_volume(ip, value=None):
        url = volume_speaker.format(ip) + '/Level'
        payload = json.dumps({"level": int(value)})
        return requests_url(url, 'put', data=payload).get('status')

    @staticmethod
    def stream(ip, mode):
        """Player Stream
        mode = 'Play', 'Pause', 'Wind', 'Rewind', 'Forward', 'Backward'
        """
        url = zone_stream.format(ip, mode)
        return requests_url(url, 'post').get('status')

    @staticmethod
    def mute(ip):
        url = volume_speaker.format(ip) + '/Muted'
        payload = json.dumps({"muted": False})
        return requests_url(url, 'put', data=payload).get('status')

    def get_product_status(self, ip):
        info = ['get_standby', 'current_source', 'muted']
        for i in info:
            self.get_info(i, ip)
        self.INFO['product_status'] = {
            'Power': self.INFO.get('standby_status'),
            'Source': self.INFO.get('current_source'),
            'Muted': 'Yes' if self.INFO.get('muted') else 'No'
        }
        return self.INFO["product_status"]

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
        return self.transfer_data("set", ip, logReport_para, timeout=80)["status"]

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
        if not check_url_status(beo_device.format(ip), timeout=5):
            return False
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
        self.saved_ip = self.load_ip()
        ip_info = WindowsWifi().discover_ips()
        scanned_ip = ip_info.get('ip')
        gateway = ip_info.get('gateway')
        ips = []
        ips.extend(self.saved_ip)
        for ip in scanned_ip:
            if ip not in self.saved_ip:
                ips.append(ip)
        # ips = list(set(self.saved_ip + scanned_ip))  # method set will not keep list order
        for ip in ips:
            tmp = ip.rsplit('.', 1)[0]
            if tmp not in gateway:
                ips = [i for i in filter(lambda x: x != ip, ips)]
        self.log.debug(ips)
        self.thread_scan_devices(ips)

        # For show device info in real-time(one by one) when scanning
        thread_status = Thread(target=self.scan_status, args=())
        thread_status.setDaemon(True)
        thread_status.start()

    def thread_scan_devices(self, ips: list):
        self.threads = []
        for ip in ips:
            t = Thread(target=self.scan_devices, args=(ip,))
            t.setDaemon(True)
            t.start()
            self.threads.append(t)
            sleep(0.005)    # avoid network block

    @staticmethod
    def load_ip():
        return load(saved_ip_path).get('ip')

    @staticmethod
    def store_ip(ips):
        # If saved ips are more than 20, then remove the oldest one (first in first out).
        if len(ips) > 20:
            ips = [i for i in filter(lambda x: x != ips[0], ips)]
        store(saved_ip_path, {"ip": ips})

    def scan_status(self):
        for td in self.threads:
            td.join()
        self.status = 1
        self.store_ip(self.saved_ip)

    def scan_devices(self, ip):
        r = requests_url(beo_device.format(ip), 'get', timeout=6)
        # if not self.check_url_status("http://{}/index.fcgi".format(ip), timeout=6):  # timeout need modify
        if r.get('status') != 200:
            return
        try:
            data = json.loads(r.get('content'), encoding='utf-8')
            beo_info = data.get('beoDevice')
            device_name = beo_info.get('productFriendlyName').get('productFriendlyName')
            model_name = beo_info.get('productId').get('productType')
            # device_name = self.get_info("device_name", ip)
            # model_name = self.get_info("basicInfo", ip)['modelName']

            """
            result = socket.gethostbyaddr(ip)
            try:
                host_name = result[0].replace(".lan", "")
            except Exception as e:
                self.log.error("host name not contain .lan" + e)
                return
            """
            if lock.acquire():
                if ip not in self.saved_ip:
                    self.saved_ip.append(ip)
                self.devices_list.append("{} ({}) [{}]".format(device_name, ip, model_name))
                # self.devices_list.append("{} ({})".format(host_name, ip))
                lock.release()
        # except socket.herror as e:
        except Exception as e:
            self.log.debug("Something wrong when scanning {}: {}".format(ip, e))
    # ==================================================================================================================

    def thread_get_info(self, ip):
        if not check_url_status(beo_device.format(ip), timeout=5):
            return {"error": "error", "ip": ip}
        # self.devices_list.clear()
        # basic_info = ase_info.get_info("basicInfo", ip)
        # beo_device_info = ase_info.get_info('BeoDevice', ip)
        self.INFO["ip"] = ip
        info = ['BeoDevice', 'modulesInformation', 'bluetoothSettings', 'get_product_status']
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
        self.INFO["ase_version"] = '{} ({})'.format(
            self.INFO.get('version'), self.INFO.get('sn'))
        self.INFO["fep_versions"] = '{} ({})'.format(
            self.INFO.get('fep_app'), self.INFO.get('bootloader'))
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
            # url = re.findall(r'http:.*tgz', content)
            url = 'http://{}/{}'.format(ip, content)
            path = os.path.join(save_path, 'log_{}.tgz'.format(sn))
            try:
                request.urlretrieve(url, path)
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
