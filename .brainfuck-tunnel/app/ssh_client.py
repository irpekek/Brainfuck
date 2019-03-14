import subprocess
from .app import *

class ssh_client(object):
    def __init__(self, inject_host_port, proxy_command):
        super(ssh_client, self).__init__()

        self.inject_host, self.inject_port = inject_host_port
        self.proxy_command = proxy_command
        self.account = {}

        self.reconnect = False

    def log(self, value, color='[G1]'):
        log_file(real_path('/../storage/app.log'), value, color=color)

    def start(self):
        while True:
            account = self.account
            host = account['host']
            port = account['port']
            username = account['username']
            password = account['password']
            sockport = account['sockport']
            proxy_command = self.proxy_command
            
            response = subprocess.Popen(
                (
                    'sshpass -p "{password}" ssh -v -CND {sockport} {host} -p {port} -l "{username}" ' + \
                    '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ProxyCommand="{}"'.format(proxy_command)
                ).format(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    sockport=sockport,
                    inject_host=self.inject_host,
                    inject_port=self.inject_port
                ),

                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )

            for line in response.stdout:
                line = line.decode().lstrip(r'(debug1|Warning):').strip() + '\r'

                if 'pledge: proc' in line:
                    self.reconnect = True
                    self.log('Connected', color='[Y1]')

                elif 'Permission denied' in line:
                    self.log('Access Denied', color='[R1]')
                    break

                elif 'Connection closed' in line:
                    self.log('Connection closed', color='[R1]')
                    break

                elif 'Could not request local forwarding' in line:
                    self.log('Port used by another programs', color='[R1]')
                    break

            self.log('Disconnected', color='[R1]')

            if self.reconnect == False: break
