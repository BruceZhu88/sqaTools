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

main_cfg_path = './config/main.conf'
main_config = Config(main_cfg_path)
main_config.cfg_load()
main_cfg = main_config.cfg

ase_ota_setting_path = main_cfg.get('WifiSpeaker', 'ase_ota_setting')
status_running = main_cfg.get('WifiSpeaker', 'status_running')
wifi_setup_ini_path = main_cfg.get('WifiSpeaker', 'wifi_setup')
wifi_setup_cfg = Config(wifi_setup_ini_path)
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
        devices_list = ase_info.return_devices()
        status = devices_list.get("status")
        devices_info = devices_list.get("devices")
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
    socketio.start_background_task(target=ase_info.get_ase_devices_list)
    socketio.start_background_task(target=scan_devices_thread)


'''
@socketio.on('connect', namespace='/wifi_speaker/test')
def test_connect():
    socketio.start_background_task(target=background_thread)
'''


@app.route('/get_info', methods=['GET'])
def get_info():
    # text = request.form.to_dict().get("text")  ---> if methods=post
    text = request.args.get("text")  # ---> if methods=get
    # p = re.compile(r'(?:(?:[0,1]?\d?\d|2[0-4]\d|25[0-5])\.){3}(?:[0,1]?\d?\d|2[0-4]\d|25[0-5])')
    try:
        ip = re.findall('\((.*)\)', text)[0]
    except:
        ip = text
    ip_address = "http://" + ip + "/index.fcgi"
    if not check_url_status(ip_address, timeout=6):
        return jsonify({"error": "error", "ip": ip})
    basic_info = ase_info.get_info("basicInfo", ip)
    beo_device = ase_info.get_info('BeoDevice', ip)
    INFO["device_versions"] = '{} ({})'.format(beo_device['version'], basic_info["appVersion"])
    INFO["sn"] = beo_device['serialNumber']
    INFO["deviceName"] = beo_device['productFriendlyName']
    INFO["bt_reconnect"] = ase_info.get_info("bt_reconnect", ip)
    INFO["bt_devices"] = ase_info.get_info('bt', ip)
    INFO["bt_open"] = ase_info.get_info('bt_open', ip)
    INFO["current_source"] = ase_info.get_current_source(ip)
    INFO["ip"] = ip
    return jsonify(INFO)


@socketio.on('bt_open', namespace='/wifi_speaker/test')
def bt_open(msg):
    ase_info.bt_open_set(msg["enable"], INFO["ip"])


@socketio.on('bt_pair', namespace='/wifi_speaker/test')
def bt_pair(msg):
    ase_info.pair_bt(msg['cmd'], INFO['ip'])


def thread_check_standby(ip):
    num = 0
    start_time = time.time()
    while PAGE_INFO['page'] == 'wifi_speaker':
        socketio.sleep(1)
        num = num + 1
        if num >= 60 * 30:   # timeout
            socketio.emit("check_standby", {"status": "timeout"}, namespace="/wifi_speaker/test")
            return
        if ase_info.get_current_source(ip) == 'Standby':
            tmp_time = time.time() - start_time
            m = int(tmp_time / 60)
            s = round(tmp_time % 60)
            decade_m = '0' if int(m / 10) == 0 else ''
            decade_s = '0' if int(s / 10) == 0 else ''
            elapsed_time = '{}{}m{}{}s'.format(decade_m, m, decade_s, s)
            socketio.emit("check_standby", {"status": "Standby", "elapsed_time": elapsed_time},
                          namespace="/wifi_speaker/test")
            return


@socketio.on('detect_standby', namespace='/wifi_speaker/test')
def detect_standby():
    socketio.start_background_task(target=thread_check_standby(INFO['ip']))


@app.route('/get_current_source', methods=['GET'])
def get_current_source():
    source = ase_info.get_current_source(INFO['ip'])
    return jsonify({'source': source})


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
    ip = request.form.to_dict().get("ip")
    product_name = request.form.to_dict().get("name")
    ase_info.change_product_name(product_name, ip)
    return jsonify({})


@app.route('/ase_reset', methods=['POST'])
def ase_reset():
    ip = request.form.to_dict().get("ip")
    ase_info.reset(ip)
    return jsonify({})


@app.route('/ase_set_bt_reconnect_mode', methods=['POST'])
def ase_set_bt_reconnect_mode():
    ip = request.form.to_dict().get("ip")
    mode = request.form.to_dict().get("mode")
    ase_info.bt_reconnect_set(mode, ip)
    return jsonify({})


@app.route('/bt_remove', methods=['POST'])
def bt_remove():
    ip = request.form.to_dict().get("ip")
    bt_mac = request.form.to_dict().get("bt_mac")
    ase_info.bt_remove(bt_mac, ip)
    return jsonify({})


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
    socketio.start_background_task(target=thread_ota_status_check(msg["ip"]))


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
    print(4)
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
    settings = {}
    wifi_setup_cfg.cfg_load()
    for info1 in wifi_setup_cfg.cfg_dump():
        for info2 in info1:
            settings[info2[0]] = info2[1]
    wifi_setup_cfg.save()
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
    wifi_setup_cfg.cfg_load()
    wifi_setup_cfg.set_items(msg)
    wifi_setup_cfg.save()
    wifi_setup = WifiSetup(INFO["ip"], INFO["deviceName"], wifi_setup_cfg,socketio)
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
    return render_template('PowerCycle.html')


def scan_port_thread():
    global serial_tool
    serial_tool = SerialTool(socketio)
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
    store(status_running, {"power_cycle_status": 1})
    serial_tool.power_cycle(msg)
    socketio.emit("stop_confirm", namespace='/power_cycle/test')


@socketio.on('auto_power_cycle', namespace='/power_cycle/test')
def auto_power_cycle(msg):
    global serial_tool
    power_cycle_cfg.cfg_load()
    power_cycle_cfg.set_items(msg)
    power_cycle_cfg.save()
    socketio.emit("start_auto_power_cycle", msg, namespace='/power_cycle/test')
    socketio.start_background_task(target=auto_power_cycle_thread(msg))


@app.route('/stop_auto_power_cycle', methods=['POST'])
def stop_auto_power_cycle():
    store(status_running, {"power_cycle_status": 0})
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
    return render_template('Automate.html')


@socketio.on('automate_cmd', namespace='/automate/test')
def automate_cmd(msg):
    command = msg["cmd"]
    auto_cmd = Command()
    auto_cmd.init_file()
    val = auto_cmd.cmd(command)
    print(val)


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
        go_web_page("http://{}:{}".format(app_setting["host"], app_setting["port"]))
        print("Server started: http://{}:{}".format(app_setting["host"], app_setting["port"]))
    socketio.run(app, host=app_setting["host"], port=app_setting["port"])
    # app.run(host='localhost', port=5000)
