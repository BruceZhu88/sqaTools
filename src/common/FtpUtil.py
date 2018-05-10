# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        checkUpdates
# Purpose:
#
# Author:      Bruce Zhu
#
# Created:     8/11/2017
# Copyright:   (c) it 2017
# Licence:     <your licence>
# -------------------------------------------------------------------------------

# cmd('disconnect bluetooth(%s)'%bt_name)
# cmd('connect bluetooth(%s)'%bt_name)
# cmd('bluetooth status()')
# cmd('PlayAudio(%s)'%musicPath)
# cmd('mediaVolumeUp()')
# cmd('mediaVolumeUp()')
# cmd('StopAudio()')
import os
from src.common.Logger import Logger
from ftplib import FTP


class FtpUtil(object):
    def __init__(self, host='', port=21, user='', pwd='', ftp_path=''):
        self.log = Logger('main').logger()
        self.ftp = FTP()
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.ftp_path = ftp_path

    def connect(self):
        try:
            self.ftp.connect(self.host, self.port)
            self.ftp.login(self.user, self.pwd)
            # print('Ftp connected!')
            return True
        except Exception as e:
            self.log.error("Error when connecting FTP server: {0}".format(e))
            return False
            # sys.exit()

    def up(self, path, filename):
        try:
            # print ftp.dir() #display file detail under directory
            # print ftp.nlst()
            if not self.connect():
                return False
            self.ftp.cwd(path)
            buf_size = 1024
            file_handler = open(filename, 'rb')
            self.ftp.storbinary('STOR %s' % os.path.basename(filename), file_handler, buf_size)
            # ftp.set_debuglevel(0)
            file_handler.close()
            self.ftp.quit()
            return True
        except Exception as e:
            self.log.error("Error when ftp_up: {0}".format(e))
            # sys.exit()
            return False

    def down(self, path, filename):
        try:
            if not self.connect():
                return False
            self.ftp.cwd(path)
            buf_size = 1024
            file_handler = open(filename, 'wb').write
            self.ftp.retrbinary('RETR %s' % os.path.basename(filename), file_handler, buf_size)
            self.ftp.set_debuglevel(0)
            # file_handler.close()
            self.ftp.quit()
            # print "ftp down OK"
            return True
        except Exception as e:
            self.log.error("Error when ftp_down: {0}".format(e))
            # sys.exit()
            return False


if __name__ == "__main__":
    ip = '192.168.0.105'
    port = 3721
    ftp = FtpUtil(host=ip, port=port, user='', pwd='', ftp_path='autoSQA/')
    print(ftp.connect())
