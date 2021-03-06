#!/usr/bin/env python
# -------------------------------------------------------------------------
# added by Bruce for packaging whole project into exe by pyinstaller

from src import *
import configparser
from dns import dnssec,e164,edns,entropy,exception,flags,inet,ipv4,ipv6,\
    message,name,namedict,node,opcode,query,rcode,rdata,rdataclass,rdataset,\
    rdatatype,renderer,resolver,reversename,rrset,tokenizer,tsig,\
    tsigkeyring,ttl,update,version,zone
import engineio.async_eventlet
# -------------------------------------------------------------------------
import subprocess
import sys
import re
import time
# import win32api
import app_config
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, jsonify, url_for, send_from_directory
from flask_socketio import SocketIO
from src.wifiSpeaker.AseInfo import AseInfo
from src.wifiSpeaker.AseUpdate import AseUpdate
from src.wifiSpeaker.WifiSetup import WifiSetup
from src.powerCycle.SerialTool import SerialTool
from src.automate.Command import Command
from src.automate.automate import Automate
from src.common.cfg import Config
from src.common.util import *
from src.common.Logger import Logger
from src.common.Url import check_url_status
from src.common.QRcode import MakeQR

logger = Logger("main").logger()
# print(__file__)  print(sys.argv[0])
# print(os.path.basename(__file__))
cmd = "tasklist|find /i \"{}.exe\"".format(os.path.basename(__file__).rsplit(".", 1)[0])
p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
tasklist = p.stdout.readlines()
if len(tasklist) > 1:
    logger.info("sqaTools.exe has been launched!")
    # win32api.MessageBox(0, "sqaTools has been launched!", "Warning")
    sys.exit()

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = "eventlet"

app = Flask(__name__)
app.config.from_object(app_config)
socketio = SocketIO(app, async_mode=async_mode)
# socketio.async_mode
ALLOWED_EXTENSIONS = set(['txt', 'ini'])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

thread_ase_ota = None
thread_setup_wifi = None
thread = None
thread_lock = threading.Lock()
serial_tool = None
ase_info = AseInfo()

INFO = {}
UNBLOCK = {}
PAGE_INFO = {"page": ""}
STOP_REFRESH = False
run_automation_steps = {}

main_cfg_path = './config/main.conf'
main_config = Config(main_cfg_path)
main_config.cfg_load()
main_cfg = main_config.cfg

ase_ota_setting_path = main_cfg.get('WifiSpeaker', 'ase_ota_setting')
power_cycle_running_status = main_cfg.get('WifiSpeaker', 'power_cycle_running_status')
wifi_setup_path = main_cfg.get('WifiSpeaker', 'wifi_setup')
automate_running_status = main_cfg.get('Automate', 'automate_running_status')
saved_action_steps = main_cfg.get('Automate', 'action_steps')
automation_cfg = Config(main_cfg.get('Automate', 'automation'))
power_cycle_cfg = Config(main_cfg.get('PowerCycle', 'power_cycle'))
cmd_get_log_file = main_cfg.get('WifiSpeaker', 'cmd_get_log_file')
ase_log_path = main_cfg.get('Log', 'ase_log_path')
script_path = main_cfg.get('WifiSpeaker', 'script_path')

qr_code_num = 0
logger.debug("Starting {}".format(os.path.basename(__file__).rsplit(".", 1)[0]))
"""
@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello1.html', name=name)
"""

"""
*********************************************************************************
                        *Index*
********************************************************************************* 
"""


@app.route('/')
def index():
    PAGE_INFO['page'] = 'home'
    global app_version
    return render_template('index.html', app_version=app_version)


"""
*********************************************************************************
                        *Wifi Speaker*
********************************************************************************* 
"""


@app.route('/wifi_speaker')
def wifi_speaker():
    PAGE_INFO['page'] = 'wifi_speaker'
    return render_template('WifiSpeaker.html')


''''
@app.route('/scan_devices', methods=['GET'])
def scan_devices():
    """
    while len(DEVICES) > 0:
        DEVICES.clear()
    device_scan = deviceScan(DEVICES)
    if device_scan.scan() == -1:
        return jsonify({"error": "error"})
    """
    devices = ase_info.get_ase_devices_list()
    return jsonify(devices)
'''


def scan_devices_thread():
    tmp_devices = ''
    while PAGE_INFO['page'] == 'wifi_speaker':
        socketio.sleep(0.003)  # avoid emmit block
        status = ase_info.status
        devices_info = ase_info.devices_list
        if len(devices_info) > 0:
            # for i in devices_info.keys():  # dict.keys() return a list, so won't crash
            for d in devices_info:
                if d not in tmp_devices:
                    socketio.sleep(0.003)
                    tmp_devices += d
                    socketio.emit('get_scan_devices', {'data': d},
                                  namespace='/wifi_speaker/test')
        if status == 1:
            socketio.emit('stop_scan_devices',
                          namespace='/wifi_speaker/test')
            return


@socketio.on('scan_devices', namespace='/wifi_speaker/test')
def scan_devices():
    socketio.start_background_task(target=scan_devices_thread)
    socketio.start_background_task(target=ase_info.get_ase_devices_list)


'''
@socketio.on('connect', namespace='/wifi_speaker/test')
def test_connect():
    socketio.start_background_task(target=background_thread)
'''


@app.route('/get_info', methods=['GET'])
def get_info():
    global INFO, STOP_REFRESH
    STOP_REFRESH = True
    # text = request.form.to_dict().get("text")  ---> if methods=post
    text = request.args.get("ip")  # ---> if methods=get
    # p = re.compile(r'(?:(?:[0,1]?\d?\d|2[0-4]\d|25[0-5])\.){3}(?:[0,1]?\d?\d|2[0-4]\d|25[0-5])')
    try:
        ip = re.findall('\((.*)\)', text)[0]
    except:
        ip = text
    INFO = ase_info.thread_get_info(ip)
    return jsonify(INFO)


@socketio.on('save_ip', namespace='/wifi_speaker/test')
def save_ip(msg):
    ip = msg.get('ip')
    ips = ase_info.load_ip()
    if ip not in ips:
        ips.append(ip)
    ase_info.store_ip(ips)


@app.route('/check_wifi', methods=['GET'])
def check_wifi():
    ip = request.args.get("ip")
    status = {'status': 'ok'}
    if not check_url_status("http://{}:8080/BeoDevice".format(ip), timeout=5):
        status = {'status': 'error'}
    return jsonify(status)


@app.route('/get_network_settings', methods=['GET'])
def get_network_settings():
    network = ase_info.get_info('network_settings', INFO['ip'])
    if network == 'NA' or network == 'error':
        return jsonify({"error": "error"})
    return jsonify(network)


@app.route('/bt_open_set', methods=['POST'])
def bt_open_set():
    enable = request.form.to_dict().get('enable')
    status = ase_info.bt_open_set(enable, INFO["ip"])
    return jsonify({'status': status})


# @socketio.on('bt_pair', namespace='/wifi_speaker/test')
@app.route('/bt_pair', methods=['POST'])
def bt_pair():
    cmd = request.form.to_dict().get('cmd')
    status = ase_info.pair_bt(cmd, INFO['ip'])
    return jsonify({'status': status})


def thread_auto_refresh(t, items):
    global STOP_REFRESH
    while PAGE_INFO['page'] == 'wifi_speaker':
        infos = {}
        socketio.sleep(int(t))
        if not check_url_status("http://{}:8080/BeoDevice".format(INFO['ip']), timeout=5):
            STOP_REFRESH = True
            socketio.emit('print_msg', {'data': 'Seems disconnected with your product!', 'color': 'red'},
                          namespace="/wifi_speaker/test")
            return
        if not STOP_REFRESH:
            for key, value in items.items():
                if value:
                    info = ase_info.get_info(key, INFO['ip'])
                    infos[key] = info
            socketio.emit('start_auto_refresh', infos, namespace="/wifi_speaker/test")
        else:
            return


@socketio.on('auto_refresh', namespace='/wifi_speaker/test')
def auto_refresh(msg):
    global STOP_REFRESH
    STOP_REFRESH = False
    with thread_lock:
        if thread is None:
            socketio.start_background_task(thread_auto_refresh, msg.get('time_interval'), msg.get('items'))


@app.route('/stop_auto_refresh', methods=['POST'])
def stop_auto_refresh():
    global STOP_REFRESH
    STOP_REFRESH = True
    return jsonify({})


def thread_check_standby(ip):
    num = 0
    start_time = time.time()
    while PAGE_INFO['page'] == 'wifi_speaker':
        if num >= 60 * 30:   # timeout
            socketio.emit("check_standby", {"status": "timeout"}, namespace="/wifi_speaker/test")
            return
        status = ase_info.get_info('get_standby', ip)
        if status == 'NA' or status == 'error':
            socketio.emit("check_standby", {"status": "error"}, namespace="/wifi_speaker/test")
            return
        if status == 'Standby':
            tmp_time = time.time() - start_time
            m = str(int(tmp_time / 60))
            s = str(int(tmp_time % 60))
            m = '0' + m if len(m) == 1 else m
            s = '0' + s if len(s) == 1 else s
            elapsed_time = '{}m{}s'.format(m, s)
            socketio.emit("check_standby", {"status": "Standby", "elapsed_time": elapsed_time},
                          namespace="/wifi_speaker/test")
            return
        socketio.sleep(1)
        num = num + 1


@socketio.on('detect_standby', namespace='/wifi_speaker/test')
def detect_standby():
    socketio.start_background_task(thread_check_standby, INFO['ip'])


@app.route('/get_product_status', methods=['GET'])
def get_product_status():
    status = ase_info.get_info('get_product_status', INFO['ip'])
    return jsonify(status)


@app.route('/get_volume', methods=['GET'])
def get_volume():
    volume = ase_info.get_info('volume', INFO['ip'])
    if volume == 'NA' or volume == 'error':
        return jsonify({"error": "error"})
    return jsonify(volume)


@app.route('/get_other_info', methods=['GET'])
def get_other_info():
    info = ase_info.get_other_info(INFO['ip'])
    return jsonify(info)


# return render_template('WifiSpeaker.html', info=info)
@app.route('/log_submit_server', methods=['POST'])
def log_submit_server():
    ip = request.form.to_dict().get("ip")
    status = ase_info.log_submit(ip)
    return jsonify({"status": status})


@app.route('/log_download_local', methods=['POST'])
def log_download_local():
    log_path = ase_info.download_log(INFO["ip"], INFO["sn"], script_path, ase_log_path)
    return jsonify({"log_path": log_path})


@app.route('/log_get', methods=['POST'])
def log_get():
    log_path = ase_info.get_log_files(INFO["ip"], INFO["sn"], cmd_get_log_file, ase_log_path)
    return jsonify({"log_path": log_path})


@app.route('/log_clear', methods=['POST'])
def log_clear():
    status = ase_info.log_clear(INFO["ip"])
    # os.system('"{} root@192.168.1.100"'.format(".\config\OpenSSH\\bin\ssh.exe"))
    return jsonify({"status": status})


@app.route('/change_product_name', methods=['POST'])
def change_product_name():
    # ip = request.form.to_dict().get("ip")
    product_name = request.form.to_dict().get("name")
    status = ase_info.change_product_name(product_name, INFO['ip'])
    return jsonify({"status": status})


@app.route('/ase_reset', methods=['POST'])
def ase_reset():
    # ip = request.form.to_dict().get("ip")
    status = ase_info.reset(INFO['ip'])
    return jsonify({'status': status})


@app.route('/ase_set_bt_reconnect_mode', methods=['POST'])
def ase_set_bt_reconnect_mode():
    # ip = request.form.to_dict().get("ip")
    mode = request.form.to_dict().get("mode")
    status = ase_info.bt_reconnect_set(mode, INFO['ip'])
    return jsonify({'status': status})


@app.route('/bt_remove', methods=['POST'])
def bt_remove():
    # ip = request.form.to_dict().get("ip")
    bt_mac = request.form.to_dict().get("bt_mac")
    status = ase_info.bt_remove(bt_mac, INFO['ip'])
    return jsonify({'status': status})


@app.route('/unblock', methods=['POST'])
def unblock():
    logger.info("Starting unblock...")
    ip = request.form.to_dict().get("ip")
    unblock_status = ase_info.unblock_device(ip)
    UNBLOCK["status"] = "successful" if unblock_status else "fail"
    return jsonify(UNBLOCK)


def thread_ota_status_check(ip):
    num = 0
    socketio.sleep(40)
    while PAGE_INFO['page'] == 'wifi_speaker':
        socketio.sleep(3)
        num = num + 1
        if num >= 60:   # 180s timeout
            socketio.emit("ota_check_over", namespace="/wifi_speaker/test")
            return
        if check_url_status("http://{}/index.fcgi".format(ip), timeout=6):
            socketio.emit("ota_check_over", namespace="/wifi_speaker/test")
            return


@socketio.on('ota_status_check', namespace='/wifi_speaker/test')
def ota_status_check(msg):
    socketio.start_background_task(thread_ota_status_check, msg["ip"])


@app.route('/one_tap_ota', methods=['POST'])
def one_tap_ota():
    status = ""
    ip = request.form.to_dict().get("ip")
    file_path = r'{}'.format(request.form.to_dict().get("file_path"))
    if not check_url_status("http://{}/index.fcgi".format(ip), timeout=6):
        return jsonify({"status": "device disconnect"})
    if not os.path.exists(file_path):
        return jsonify({"status": "file error"})
    files = {
        'file': open(file_path, 'rb')
    }
    if ase_info.ota_update(ip, files) == 200:
        status = ase_info.trigger_update(ip)
    else:
        logger.debug("Upload ASE OTA file failed!")
    return jsonify({"status": status})


@app.route('/page_info', methods=['GET'])
def page_info():
    return jsonify(PAGE_INFO)


@app.route('/get_ota_setting', methods=['GET'])
def get_ota_setting():
    settings = load(ase_ota_setting_path)
    return jsonify(settings)


'''
@app.route('/ota_auto_update', methods=['GET', 'POST'])
def ota_auto_update():
    error = None
    if request.method == 'POST':
        store(status_json, {"aseOtaUpdate": "1"})
        setting_values = request.form.to_dict()
        store(ase_ota_setting_path, setting_values)
        _thread.start_new_thread(aseUpdate(socketio).start_ota, ())
        return jsonify({"": ""})
    else:
        return redirect(url_for('wifi_speaker'))
'''


def ase_ota_thread():
    while PAGE_INFO['page'] == 'wifi_speaker':
        socketio.sleep(1)
        if not thread_ase_ota.is_alive():
            socketio.emit("stop_ase_auto_update", namespace='/wifi_speaker/test')
            return


@socketio.on('ota_auto_update', namespace='/wifi_speaker/test')
def ota_auto_update(msg):
    global thread_ase_ota
    store(ase_ota_setting_path, msg)
    # thread.start_new_thread(aseUpdate(socketio).start_ota, ())
    with thread_lock:
        thread_ase_ota = socketio.start_background_task(target=AseUpdate(socketio, ase_ota_setting_path).start_ota)
        socketio.start_background_task(target=ase_ota_thread)


@app.route('/wifi_setup_setting', methods=['GET'])
def wifi_setup_setting():
    """
    :return:
    """
    '''
    settings = {}
    wifi_setup_cfg.cfg_load()
    for info1 in wifi_setup_cfg.cfg_dump():
        for info2 in info1:
            settings[info2[0]] = info2[1]
    wifi_setup_cfg.save()
    '''
    settings = load(wifi_setup_path)
    if len(settings) == 0:
        settings['dhcp'] = 'True'
    return jsonify(settings)


def auto_setup_wifi_thread():
    while PAGE_INFO['page'] == 'wifi_speaker':
        socketio.sleep(1)
        if not thread_setup_wifi.is_alive():
            socketio.emit("stop_auto_setup_wifi", namespace='/wifi_speaker/test')
            return


@socketio.on('auto_setup_wifi', namespace='/wifi_speaker/test')
def auto_setup_wifi(msg):
    global thread_setup_wifi
    '''
    wifi_setup_cfg.cfg_load()
    wifi_setup_cfg.set_items(msg)
    wifi_setup_cfg.save()
    '''
    store(wifi_setup_path, msg)
    wifi_setup = WifiSetup(INFO["ip"], INFO["deviceName"], wifi_setup_path, socketio)
    thread_setup_wifi = socketio.start_background_task(target=wifi_setup.setup)
    socketio.start_background_task(target=auto_setup_wifi_thread)


@app.route('/exit_run')
def exit_run():
    return redirect(url_for('wifi_speaker'))


"""
@app.before_request
def my_before_request():
    status = load(status_json)["aseOtaUpdate"]
    if status=="1":
        return render_template('aseOtaStatus.html')
"""


@app.route('/check_ota_path', methods=['POST'])
def check_ota_path():
    msg = request.form.to_dict()
    for n in msg:
        path = msg[n]
        if not (os.path.isfile(path) and os.stat(path)):
            return jsonify({"status": "error", "name": n})
    return jsonify({"status": "ok"})


"""
*********************************************************************************
                        *Power Cycle*
********************************************************************************* 
"""


@app.route('/power_cycle')
def power_cycle():
    PAGE_INFO['page'] = 'power_cycle'
    store(power_cycle_running_status, {"power_cycle_status": 0})
    return render_template('PowerCycle.html')


def scan_port_thread():
    global serial_tool
    serial_tool = SerialTool(power_cycle_running_status, socketio)
    while PAGE_INFO['page'] == 'power_cycle':
        serial_tool.find_all_serial()
        socketio.sleep(1.2)


@socketio.on('scan_port', namespace='/power_cycle/test')
def scan_port():
    socketio.start_background_task(target=scan_port_thread)


@socketio.on('open_port', namespace='/power_cycle/test')
def open_port(msg):
    global serial_tool
    serial_tool.open_port(msg)


@socketio.on('close_port', namespace='/power_cycle/test')
def close_port():
    global serial_tool
    serial_tool.close_port()


@socketio.on('send_ser_msg', namespace='/power_cycle/test')
def send_ser_msg(msg):
    global serial_tool
    serial_tool.send_msg(msg["msg"], False)


@app.route('/power_cycle_options', methods=['GET'])
def power_cycle_options():
    settings = {}
    power_cycle_cfg.cfg_load()
    for info1 in power_cycle_cfg.cfg_dump():
        for info2 in info1:
            settings[info2[0]] = info2[1]
    power_cycle_cfg.save()
    return jsonify(settings)


def auto_power_cycle_thread(msg):
    global serial_tool
    store(power_cycle_running_status, {"power_cycle_status": 1})
    serial_tool.power_cycle(msg)
    socketio.emit("stop_confirm", namespace='/power_cycle/test')


@socketio.on('auto_power_cycle', namespace='/power_cycle/test')
def auto_power_cycle(msg):
    global serial_tool
    power_cycle_cfg.cfg_load()
    power_cycle_cfg.set_items(msg)
    power_cycle_cfg.save()
    socketio.emit("start_auto_power_cycle", msg, namespace='/power_cycle/test')
    socketio.start_background_task(auto_power_cycle_thread, msg)


@app.route('/stop_auto_power_cycle', methods=['POST'])
def stop_auto_power_cycle():
    store(power_cycle_running_status, {"power_cycle_status": 0})
    # here cannot use socketio to send stop command as some block will happen and cannot get command immediately!
    socketio.emit("stop_auto_power_cycle", namespace='/power_cycle/test')
    return jsonify({"status": "stopped"})


"""
*********************************************************************************
                        *Automate command*
********************************************************************************* 
"""


@app.route('/automate')
def automate():
    PAGE_INFO['page'] = 'automate'
    store(automate_running_status, {"run_state": 0})
    return render_template('Automate.html')


@socketio.on('automate_cmd', namespace='/automate/test')
def automate_cmd(msg):
    command = msg["cmd"]
    auto_cmd = Command()
    auto_cmd.init_file()
    val = auto_cmd.cmd(command)
    print(val)


@app.route('/automate/get_automation_info', methods=['GET'])
def get_automation_info():
    automation_cfg.cfg_load()
    bp_port = automation_cfg.cfg.get('Button_Press', 'bp_port')
    bp_time = automation_cfg.cfg.get('Button_Press', 'bp_time')
    bp_usb_port = automation_cfg.cfg.get('Button_Press', 'bp_usb_port')
    ac_usb_port = automation_cfg.cfg.get('AC_Power', 'ac_usb_port')
    ac_state = automation_cfg.cfg.get('AC_Power', 'ac_state')
    d_time = automation_cfg.cfg.get('Delay', 'd_time')
    ase_volume = automation_cfg.cfg.get('ASE', 'volume')
    ase_ip = automation_cfg.cfg.get('ASE', 'ip')
    check_volume = automation_cfg.cfg.get('ASE', 'check_volume')
    check_playback = automation_cfg.cfg.get('ASE', 'check_playback')
    check_power_state = automation_cfg.cfg.get('ASE', 'check_power_state')
    check_network = automation_cfg.cfg.get('ASE', 'check_network')
    check_source = automation_cfg.cfg.get('ASE', 'check_source')
    check_bt_connection = automation_cfg.cfg.get('ASE', 'check_bt_connection')
    automation_cfg.save()
    info1 = {
        "button_press": "Button Press (Port:{}, Time:{})".format(bp_port, bp_time),
        "ac_power": "AC Power (State:{})".format(ac_state),
        "delay": "Delay (Time:{})".format(d_time),
        "set_volume": "Set Volume (Value:{})".format(ase_volume),
        'do_check_volume': "Check Volume (Value:{})".format(check_volume),
        'do_check_playback': "Check Playback (Value:{})".format(check_playback),
        'do_check_power_state': 'Check Power State (Value:{})'.format(check_power_state),
        'do_check_network': 'Check Network Connection(Value:{})'.format(check_network),
        'do_check_source': 'Check Source (Value:{})'.format(check_source),
        'do_check_bt_connection': 'Check BT Connection(Value:{})'.format(check_bt_connection),
    }
    info2 = {
        'bp_port': bp_port,
        'bp_time': bp_time,
        'ac_state': ac_state,
        "d_time": d_time,
        "volume": ase_volume,
        "ip": ase_ip,
        'bp_usb_port': bp_usb_port,
        'ac_usb_port': ac_usb_port,
        'check_volume': check_volume,
        'check_playback': check_playback,
        'check_power_state': check_power_state,
        'check_network': check_network,
        'check_source': check_source,
        'check_bt_connection': check_bt_connection
    }
    info = {
        'info1': info1,
        'info2': info2
    }
    return jsonify(info)


@app.route('/automate/save_automation_info', methods=['POST'])
def save_automation_info():
    info = request.form.to_dict()
    automation_cfg.cfg_load()
    automation_cfg.set_items(info)
    automation_cfg.save()
    return jsonify({})


def run_automation_thread(msg):
    auto = Automate(automation_cfg, automate_running_status, socketio)
    store(automate_running_status, {"run_state": 1})
    socketio.sleep(0.1)
    auto.run(msg)


@socketio.on('start_run_automation', namespace='/automate/test')
def start_run_automation(msg):
    global run_automation_steps
    run_automation_steps = msg
    socketio.start_background_task(run_automation_thread, msg)


@app.route('/automate/stop_automation_running', methods=['POST'])
def stop_automation_running():
    store(automate_running_status, {"run_state": 0})
    # here cannot use socketio to send stop command as some block will happen and cannot get command immediately!
    return jsonify({"status": "stopped"})


@socketio.on('save_steps', namespace='/automate/test')
def start_run_automation(msg):
    file_name = msg.get('file_name')
    file_path = os.path.join(saved_action_steps, '{}.json'.format(file_name))
    with open(file_path, 'w') as f:
        f.write('')
    store(file_path, msg.get('steps'))
    socketio.emit('save_success', {'file_name': file_name}, namespace='/automate/test')


@app.route('/automate/load_steps', methods=['GET'])
def load_steps():
    path = saved_action_steps
    all_files = []
    for root, dirs, files in os.walk(path):
        for filename in files:
            all_files.append(filename.rsplit('.', 1)[0])
    if len(all_files) == 0:
        return jsonify({})
    return jsonify({'files_name': all_files})


@app.route('/automate/remove_saved_list', methods=['POST'])
def remove_saved_list():
    path = saved_action_steps
    file_name = request.form.to_dict().get('name')
    file_path = os.path.join(path, file_name.rsplit('_', 1)[0] + '.json')
    if os.path.isfile(file_path):
        os.remove(file_path)
    return jsonify({})


@app.route('/automate/load_step', methods=['POST'])
def load_step():
    info = {}
    path = saved_action_steps
    file_name = request.form.to_dict().get('name')
    file_path = os.path.join(path, file_name.rsplit('__', 1)[0] + '.json')
    if os.path.isfile(file_path):
        info = load(file_path)
    return jsonify(info)


"""
*********************************************************************************
                        *Data Graph*
********************************************************************************* 
"""


@app.route('/DataGraph/')
def data_graph(data_name=None):
    if data_name is None:
        data_name = "demo.txt"
    PAGE_INFO['page'] = 'DataGraph'
    return render_template('DataGraph.html', name=data_name)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/DataGraph/upload_file', methods=['GET', 'POST'])
def upload_file():
    file_url = ""
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # file_url = url_for('uploaded_file', filename=filename)
            file_url = filename
            # return html + '<br><img src=' + file_url + '>'
            # return jsonify({"errno": 0, "errmsg": "上传成功", "filename": filename})
    return render_template("DataGraph.html", name=file_url)


@app.route('/DataGraph/get_graph_data', methods=['POST'])
def get_graph_data():
    file_name = request.form.to_dict().get("filename")
    data_time = []
    data_values = []
    title = ""
    unit_name = ""
    file_error = ""
    with open("data/uploads/" + file_name, 'r') as f:
        for idx, line in enumerate(f, 1):
            try:
                if line.startswith('#'):
                    title = re.findall(r"#title:(.*)\[", line)[0]
                    unit_name = re.findall(r"\[(.*)\]", line)[0]
                    continue
                s = line.replace("\n", "").split(": ")
                data_time.append(s[0])
                data_values.append(s[1].replace(" ", ""))
            except Exception as e:
                file_error = "[{}] Line {}: Parse error: {}".format(file_name, idx, e)
                logger.debug(file_error)
        # socketio.emit("new_mychart", {"time": data_time, "values": data_values}, namespace='/DataGraph/test')
    return jsonify({"time": data_time, "values": data_values, "title": title, "name": unit_name,
                    "file_error": file_error})


"""
*********************************************************************************
                        *QR Code*
********************************************************************************* 
"""


@app.route('/QR_Code')
def qr_code():
    return render_template('QR.html')


@app.route('/QR_Code/generate', methods=['POST'])
def generate():
    global qr_code_num
    txt = request.form.to_dict().get("txt")
    qr_path = "./static/images/"
    for parent, dirs, files in os.walk(qr_path):
        for filename in files:
            obj = re.search(r'qr_(.*).jpeg', filename)
            if obj is not None:
                os.remove(qr_path + obj.group())
    qr_code_num = qr_code_num + 1
    pic = "qr_{}.jpeg".format(qr_code_num)
    make_qr = MakeQR(qr_path + pic, box_size=5)
    make_qr.generate(txt)
    return jsonify({"pic": pic})


"""
*********************************************************************************
                        *Common*
********************************************************************************* 
"""


@socketio.on('WinSCP', namespace='/test')
def win_scp():
    path = '"{}\config\WinSCP\WinSCP.exe"'.format(os.getcwd())
    # win32api.ShellExecute(0, 'open', path, '', '', 1)


if __name__ == '__main__':
    app_setting = load("./data/app.json")
    app_version = app_setting["version"]
    if not app.config["DEBUG"]:
        go_web_page("http://localhost:{}".format(app_setting["port"]))
        print("Server started: http://localhost:{}".format(app_setting["port"]))
    socketio.run(app, host=app_setting["host"], port=app_setting["port"])
    # app.run(host='localhost', port=5000)
