import os
import json
from src.common.util import store
from src.common.util import zip_dir
from src.common.cfg import Config


main_cfg_path = './config/main.conf'
main_config = Config(main_cfg_path)
main_config.cfg_load()
main_cfg = main_config.cfg

ase_ota_setting_path = main_cfg.get('WifiSpeaker', 'ase_ota_setting')
wifi_setup_path = main_cfg.get('WifiSpeaker', 'wifi_setup')
saved_ip_path = main_cfg.get('WifiSpeaker', 'saved_ip')
# clear data in test (OTA, Wifi Setup)
store(ase_ota_setting_path, {})
store(wifi_setup_path, {})
store(saved_ip_path, {"ip": []})

app_info = './data/app.json'
with open(app_info) as json_file:
    data = json.load(json_file)

app_name = data["name"]
app_version = data['version']
os.system("{}\pyinstaller_exe.bat".format(os.getcwd()))
dir_path = "./dist/run/"
zip_filename = "{0}_v{1}_x64.zip".format(app_name, app_version)
zip_dir(dir_path, zip_filename)
