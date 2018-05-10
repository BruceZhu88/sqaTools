
import subprocess


class SshHelper(object):
    """docstring for sshHelper"""

    def __init__(self, ip, user, ssh_rsa, ssh_path):
        self.ip = ip
        self.user = user
        self.ssh_path = ssh_path
        with open(ssh_rsa, 'r') as f:
            self.rsa = f.readline()

    def check_known_hosts(self):
        flag = 0
        known_hosts = '{}/.ssh/known_hosts'.format(self.ssh_path)
        with open(known_hosts, 'r') as f:
            for l in f.readlines():
                if self.ip in l:
                    flag = 1
        if flag == 0:
            with open(known_hosts, 'a') as f:
                txt = '{} ssh-rsa {}\n'.format(self.ip, self.rsa)
                f.write(txt)

    def execute(self, command):
        self.check_known_hosts()
        cmd = '{}/bin/ssh.exe {}@{} {}'.format(
            self.ssh_path, self.user, self.ip, command)
        try:
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            content = p.stdout.read().decode("utf-8")
        except Exception as e:
            content = None
        return content
