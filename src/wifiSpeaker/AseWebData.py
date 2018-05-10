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

beo_device = "http://{}:8080/BeoDevice/"
current_source = "http://{}:8080/BeoZone/Zone/ActiveSourceType"
# {"sourceType":{"type":"BLUETOOTH"},"friendlyName":"Bluetooth"}


def bt_remove_para(bt_mac):
    return {
        "path": "bluetooth:devices/" + bt_mac + "/unpair",
        "roles": "activate",
        "value": {"type": "bool_", "bool_": True}
    }


def set_device_name(name):
    return {"path": "settings:/deviceName", "roles": "value",
            "value": {"type": "string_", "string_": name}}


def set_pairing_mode(enable):
    return {"path": "settings:/bluetooth/pairingAlwaysEnabled", "roles": "value",
            "value": {"type": "bool_", "bool_": enable}}


def set_bt_mode(mode):
    return {"path": "settings:/bluetooth/autoConnect", "roles": "value",
            "value": {"type": "bluetoothAutoConnectMode", "bluetoothAutoConnectMode": mode}}
