import logging.config
import os


class Logger(object):
    
    def __init__(self, log_name):
        self.log_name = log_name
        log_path = '.\\log'
        if not os.path.exists(log_path):
            os.mkdir(log_path)
        logging.config.fileConfig("./config/logger_{}.conf".format(self.log_name))

    # config = {    "key1":"value1"     }
    def logger(self):
        return logging.getLogger(self.log_name)
