import socket
import threading
from .app import *
from .tunnel import *

class inject(threading.Thread):
    def __init__(self, host_port, tunnel_type):
        super(inject, self).__init__()

        self.socket_inject = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host, self.port = self.host_port = host_port
        self.tunnel_type = tunnel_type
        self.daemon = True

    def log(self, value, color='[G1]'):
        log_file(real_path('/../storage/app.log'), value, color=color)

    def run(self):
        try:
            self.socket_inject.bind(self.host_port)
            self.socket_inject.listen(True)
            self.log('Inject running on {} port {}'.format(self.host, self.port))
            while True: tunnel(self.socket_inject.accept(), self.tunnel_type).start()
        except OSError:
            self.log('Inject not running on {} port {} because port used by another programs'.format(self.host, self.port), color='[R1]')
