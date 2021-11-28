import re
import ssl
import time
import random
import select
import socket
import threading
from .app import *


class tunnel(threading.Thread):
    def __init__(self, socket_accept, tunnel_type):
        super(tunnel, self).__init__()

        self.socket_accept = socket_accept
        self.tunnel_type = tunnel_type

        self.do_handshake_on_connect = True
        self.buffer_size = 65535
        self.timeout = 3
        self.daemon = True

    def log(self, value, color='[G1]'):
        log_file(real_path('/../storage/app.log'), value, color=color)

    def get_socket_client(self):
        socket_client, null = self.socket_accept
        socket_client_request = socket_client.recv(
            self.buffer_size).decode('charmap')
        self.host, self.port = re.findall(
            r'([^\s]+):([^\s]+)', socket_client_request)[0]
        self.host, self.port = str(self.host), int(self.port)

        return socket_client

    def get_host_port(self, host_port):
        value = re.findall(r'([^\s]+):([^\s]+)', host_port)
        value = value[0] if len(value) else []
        value_host = value[0] if len(value) >= 1 and value[0] else ''
        value_port = value[1] if len(value) >= 2 and value[1] else '80'

        return (str(value_host), int(value_port)) if value_host and value_port else ''

    def get_proxy(self):
        data_proxies = open(real_path('/../config/proxies.txt')).readlines()
        proxies = []
        for proxy in data_proxies:
            proxy = self.get_host_port(proxy)
            if proxy:
                proxies.append(proxy)
        proxy_host, proxy_port = random.choice(proxies)

        return str(proxy_host), int(proxy_port)

    def get_payload(self):
        return open(real_path('/../config/payload.txt')).readlines()[0].strip()

    def get_server_name_indication(self):
        return open(real_path('/../config/server-name-indication.txt')).readlines()[0].strip()

    #
    #

    def payload_decode(self, payload):
        payload = payload.replace('[real_raw]', '[raw][crlf][crlf]')
        payload = payload.replace('[raw]', '[method] [host_port] [protocol]')
        payload = payload.replace('[method]', 'CONNECT')
        payload = payload.replace('[host_port]', '[host]:[port]')
        payload = payload.replace('[host]', str(self.host))
        payload = payload.replace('[port]', str(self.port))
        payload = payload.replace('[protocol]', 'HTTP/1.0')
        payload = payload.replace('[user-agent]', 'User-Agent: Chrome/1.1.3')
        payload = payload.replace('[keep-alive]', 'Connection: Keep-Alive')
        payload = payload.replace('[close]', 'Connection: Close')
        payload = payload.replace('[crlf]', '[cr][lf]')
        payload = payload.replace('[lfcr]', '[lf][cr]')
        payload = payload.replace('[cr]', '\r')
        payload = payload.replace('[lf]', '\n')

        return payload.encode()

    def send_payload(self, payload_encode=''):
        payload_encode = payload_encode if payload_encode else '[method] [host_port] [protocol][crlf][crlf]'
        self.log('Payload: \n\n{}\n'.format(('|   ' + self.payload_decode(payload_encode).decode())
                                            .replace('\r', '')
                                            .replace('[split]', '$lf\n')
                                            .replace('\n', '\n|   ')
                                            .replace('$lf', '\n')
                                            ))
        payload_split = payload_encode.split('[split]')
        for i in range(len(payload_split)):
            if i > 0:
                time.sleep(0.200)
            self.socket_tunnel.sendall(self.payload_decode(payload_split[i]))

    #
    #

    def convert_response(self, response):
        response = response.replace('\r', '').rstrip() + '\n\n'

        if response.startswith('HTTP'):
            response = '\n\n|   {}\n'.format(response.replace('\n', '\n|   '))
        else:
            response = '[W2]\n\n{}\n'.format(
                re.sub(r'\s+', ' ', response.replace('\n', '[CC][Y1]\\n[W2]')))

        return response

    def handler(self):
        sockets = [self.socket_tunnel, self.socket_client]
        timeout = 0
        self.socket_client.sendall(
            b'HTTP/1.0 200 Connection established\r\n\r\n')
        self.log('Connection established')
        while True:
            timeout += 1
            socket_io, null, errors = select.select(sockets, [], sockets, 3)
            if errors:
                break
            if socket_io:
                for socket in socket_io:
                    try:
                        data = socket.recv(self.buffer_size)
                        if not data:
                            break
                        if socket is self.socket_tunnel:
                            self.socket_client.sendall(data)
                        elif socket is self.socket_client:
                            self.socket_tunnel.sendall(data)
                        timeout = 0
                    except:
                        break
            if timeout == 30:
                break

    def proxy_handler(self):
        x = 0
        while True:
            if x == 1:
                self.log('Replacing response')
            response = self.socket_tunnel.recv(
                self.buffer_size).decode('charmap')
            if not response:
                break
            response_status = response.replace('\r', '').split('\n')[0]
            if re.match(r'HTTP/\d(\.\d)? 200 .+', response_status):
                self.log('Response: {}'.format(
                    self.convert_response(response)))
                self.handler()
                break
            else:
                self.log('Response: {}'.format(
                    self.convert_response(response)))
                self.socket_tunnel.sendall(
                    b'HTTP/1.0 200 Connection established\r\nConnection: keep-alive\r\n\r\n')
                x += 1

    def certificate(self):
        self.log('Certificate:\n\n{}'.format(
            ssl.DER_cert_to_PEM_cert(self.socket_tunnel.getpeercert(True))))

    #
    #

    # Direct -> SSH
    def tunnel_type_0(self):
        try:
            self.payload = self.get_payload()

            self.log('Connecting to {} port {}'.format(self.host, self.port))
            self.socket_tunnel.connect((self.host, self.port))
            self.send_payload(self.payload)
            self.handler()
        except socket.timeout:
            pass
        except socket.error:
            pass
        finally:
            self.socket_tunnel.close()
            self.socket_client.close()

    # Direct -> SSH (SSL/TLS)
    def tunnel_type_1(self):
        try:
            self.server_name_indication = self.get_server_name_indication()

            self.log('Connecting to {} port {}'.format(self.host, self.port))
            self.socket_tunnel.connect((self.host, self.port))
            self.log('Server name indication: {}'.format(
                self.server_name_indication))
            self.socket_tunnel = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2).wrap_socket(
                self.socket_tunnel, server_hostname=self.server_name_indication, do_handshake_on_connect=self.do_handshake_on_connect)
            self.certificate()
            self.handler()
        except socket.timeout:
            pass
        except socket.error:
            pass
        finally:
            self.socket_tunnel.close()
            self.socket_client.close()

    # HTTP Proxy -> SSH
    def tunnel_type_2(self):
        try:
            self.proxy_host, self.proxy_port = self.get_proxy()
            self.payload = self.get_payload()

            self.log('Connecting to remote proxy {} port {}'.format(
                self.proxy_host, self.proxy_port))
            self.socket_tunnel.connect((self.proxy_host, self.proxy_port))
            self.log('Connecting to {} port {}'.format(self.host, self.port))
            self.send_payload(self.payload)
            self.proxy_handler()
        except socket.timeout:
            pass
        except socket.error:
            pass
        finally:
            self.socket_tunnel.close()
            self.socket_client.close()

    # Direct -> SSH (SSL/TLS) + Payload
    def tunnel_type_3(self):
        try:
            self.server_name_indication = self.get_server_name_indication()
            self.payload = self.get_payload()

            self.log('Connecting to {} port {}'.format(self.host, self.port))
            self.socket_tunnel.connect((self.host, self.port))
            self.log('Server name indication: {}'.format(
                self.server_name_indication))
            self.socket_tunnel = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2).wrap_socket(
                self.socket_tunnel, server_hostname=self.server_name_indication, do_handshake_on_connect=self.do_handshake_on_connect)
            self.send_payload(self.payload)
            self.handler()
        except socket.timeout:
            pass
        except socket.error:
            pass
        finally:
            self.socket_tunnel.close()
            self.socket_client.close()

    # HTTP Proxy -> SSH (SSL/TLS) + Payload
    def tunnel_type_4(self):
        try:
            self.server_name_indication = self.get_server_name_indication()
            self.proxy_host, self.proxy_port = self.get_proxy()
            self.payload = self.get_payload()

            self.log('Connecting to remote proxy {} port {}'.format(
                self.proxy_host, self.proxy_port))
            self.socket_tunnel.connect((self.proxy_host, self.proxy_port))
            self.log('Server name indication: {}'.format(
                self.server_name_indication))
            self.socket_tunnel = ssl.SSLContext(ssl.PROTOCOL_TLS).wrap_socket(
                self.socket_tunnel, server_hostname=self.server_name_indication, do_handshake_on_connect=self.do_handshake_on_connect)

            self.certificate()
            self.send_payload(self.payload)
            self.handler()
        except socket.timeout:
            pass
        except socket.error:
            pass
        finally:
            self.socket_tunnel.close()
            self.socket_client.close()

    def run(self):
        self.socket_tunnel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_tunnel.settimeout(self.timeout)
        self.socket_client = self.get_socket_client()

        if not self.tunnel_type:
            pass
        elif self.tunnel_type == '0':
            self.tunnel_type_0()
        elif self.tunnel_type == '1':
            self.tunnel_type_1()
        elif self.tunnel_type == '2':
            self.tunnel_type_2()
        elif self.tunnel_type == '3':
            self.tunnel_type_3()
        elif self.tunnel_type == '4':
            self.tunnel_type_4()
