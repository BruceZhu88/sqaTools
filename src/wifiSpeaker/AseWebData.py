deviceName_para = {"path": "settings:/deviceName",
                   "roles": "value"}
displayVersion_para = {"path": "/system/displayVersion", "roles": "value"}
pairBT_para = {"path": "bluetooth:externalDiscoverable",
               "roles": "activate",
               "value": {"type": "bool_", "bool_": True}}
pairCancelBT_para = {"path": "bluetooth:externalDiscoverable",
                     "roles": "activate",
                     "value": {"type": "bool_", "bool_": False}}
pairingAlwaysEnabled_para = {"path": "settings:/bluetooth/pairingAlwaysEnabled", "roles": "value"}
autoConnect_para = {"path": "settings:/bluetooth/autoConnect", "roles": "value"}
pairedPlayers_para = {"path": "bluetooth:pairedPlayers", "roles": "title,id,description", "from": 0, "to": 99}

WirelessSSID_para = {"path": "networkWizard:info/WirelessSSID", "roles": "value"}
wifiSignalLevel_para = {"path": "settings:beo/wifiSignalLevel", "roles": "value"}
volumeDefault_para = {"path": "settings:/mediaPlayer/volumeDefault", "roles": "value"}
volumeMax_para = {"path": "settings:/mediaPlayer/volumeMax", "roles": "value"}

network_scan_results_para = {"path": "network:scan_results", "roles": "title,value", "from": 0, "to": 99}

factoryResetRequest_para = {"path": "beo_LocalUI:factoryResetRequest", "roles": "activate",
                            "value": {"type": "bool_", "bool_": True}}

logReport_para = {
    "path": "BeoPortal:logReport/send",
    "roles": "activate",
    "value": {"type": "bool_", "bool_": True}
}

update_para = {
    "path": "firmwareUpdate:update",
    "roles": "accept",
    "value": {"type": "string_", "string_": ""}
}

clearLogs_para = {
    "path": "systemManager:clearLogs",
    "roles": "activate",
    "value": {"type": "bool_", "bool_": True}
}

# location: HK
# region: None
# timezone: Asia/Hong_Kong
location_para = {
    "path": "settings:/location",
    "roles": "value",
    "value": {"type": "string_", "string_": "HK"}
}

timezone_para = {
    "path": "settings:/timezone",
    "roles": "value",
    "value": {"type": "string_", "string_": "Asia/Hong_Kong"}
}

# location: CN
# region: Shanghai
# timezone: Asia/Shanghai
'''
path: settings:/region
roles: value
value: {"type":"string_","string_":"Asia/Shanghai"}
'''

# setData
# "Tue May 22 10:14:32 2018"
time_manager_para = {
    "path": "time_manager:/get/actual/local/time/request",
    "roles": "activate",
    "value": {"type": "bool_", "bool_": True}
}


beo_device = "http://{}:8080/BeoDevice/"
sys_products = "http://{}:8080/BeoZone/System/Products"
modules_info = "http://{}:8080/BeoDevice/modulesInformation"
current_source = "http://{}:8080/BeoZone/Zone/ActiveSourceType"
# {"sourceType":{"type":"BLUETOOTH"},"friendlyName":"Bluetooth"}
network_settings = "http://{}:8080/BeoDevice/networkSettings"
bluetooth_settings = "http://{}:8080/BeoDevice/bluetoothSettings"
standby_status = "http://{}:8080/BeoDevice/powerManagement/standby"
# "standby":{"powerState":"standby"

volume_speaker = "http://{}:8080/BeoZone/Zone/Sound/Volume/Speaker"
zone_stream = "http://{}:8080/BeoZone/Zone/Stream/{}"
power_management = "http://{}:8080/BeoDevice/powerManagement"

regional_settings = "http://{}:8080/BeoDevice/regionalSettings"

white_space = '_0_white_space_0_'


def wifi_settings(ssid, key, encryption, dhcp, ip, gateway, netmask):
    # _0_white_space_0_ is temporarily replace " ", because " " will be encoded to "+" when urlencode
    ssid = ssid.replace(' ', white_space)
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
    return wifi_value


def bt_remove_para(bt_mac):
    return {
        "path": "bluetooth:devices/" + bt_mac + "/unpair",
        "roles": "activate",
        "value": {"type": "bool_", "bool_": True}
    }


def set_device_name(name):
    name = name.replace(' ', white_space)
    return {"path": "settings:/deviceName", "roles": "value",
            "value": {"type": "string_", "string_": name}}


def set_pairing_mode(enable):
    return {"path": "settings:/bluetooth/pairingAlwaysEnabled", "roles": "value",
            "value": {"type": "bool_", "bool_": enable}}


def set_bt_mode(mode):
    return {"path": "settings:/bluetooth/autoConnect", "roles": "value",
            "value": {"type": "bluetoothAutoConnectMode", "bluetoothAutoConnectMode": mode}}
