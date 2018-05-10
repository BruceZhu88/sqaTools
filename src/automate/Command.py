
from time import sleep
from src.common.FtpUtil import FtpUtil
from src.common.util import read_file
from src.common.cfg import Config


ftp_settings = Config('./data/ftp.ini')


class Command(object):
    def __init__(self):
        ftp_settings.cfg_load()
        host = ftp_settings.cfg.get("FTP", "host")
        port = ftp_settings.cfg.getint("FTP", "port")
        user = ftp_settings.cfg.get("FTP", "user")
        pwd = ftp_settings.cfg.get("FTP", "pwd")
        self.ftp_path = ftp_settings.cfg.get("FTP", "ftp_path")
        ftp_settings.save()
        self.ftp = FtpUtil(host=host, port=port, user=user, pwd=pwd, ftp_path=self.ftp_path)
        self.file_path = ".\\data\\"

    def init_file(self):
        with open(self.file_path + 'cmd.ini', 'w') as f:
            f.write("0")
        with open(self.file_path + 'return.ini', 'w') as f:
            f.write("-1")
        self.ftp.up(self.ftp_path, self.file_path + 'cmd.ini')
        self.ftp.up(self.ftp_path, self.file_path + 'return.ini')

    def cmd(self, c):
        with open(self.file_path + 'cmd.ini', 'w') as f:
            f.write(c)
        for i in range(0, 5):  # try 5 times
            if self.ftp.up(self.ftp_path, self.file_path + 'cmd.ini'):
                break
            if i == 4:
                return False
            else:
                sleep(1)
        value = '-1'
        i = 0
        while value == '-1':
            i += 1
            if i > 50:
                return False
            if self.ftp.down(self.ftp_path, self.file_path + 'return.ini'):
                value = read_file(self.file_path + 'return.ini')
                sleep(0.5)
            else:
                return False
        return value

