import os
import json
import threading
import webbrowser
from src.common.Logger import Logger
logger = Logger("main").logger()


def store(file_name, data):
    with open(file_name, 'w') as json_file:
        # json.dump(json.dumps(data), json_file)
        json_file.write(json.dumps(data))


def load(file_name):
    with open(file_name) as json_file:
        data = json.load(json_file)
    return data


def go_web_page(url):
    try:
        threading.Timer(0, lambda: webbrowser.open(url)).start()
    except Exception as e:
        logger.debug(e)


def read_file(filename):
    try:
        with open(filename) as f:
            for line in f.readlines():
                return line
    except Exception as e:
        logger.debug("File {0} does not exist: {1}".format(filename, e))
        return ""


def delete_file(src):
    if os.path.exists(src):
        try:
            os.remove(src)
        except Exception as e:
            logger.debug("Delete file {0} failed: {1}".format(src, e))
            # print('delete file %s failed'%src)
    else:
        logger.debug("Delete file {0} does not exist!!".format(src))
