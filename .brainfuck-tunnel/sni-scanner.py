import ssl
import sys
import socket
from app import app

def main():
    host = str('3.85.154.144')
    port = int('443')
    server_name_indication = sys.argv[1]

    try:
        socket_tunnel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_tunnel.settimeout(3)
        app.log('Connecting to {} port {}'.format(host, port))
        socket_tunnel.connect((host, port))
        app.log('Server name indication: {}'.format(server_name_indication))
        socket_tunnel = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2).wrap_socket(socket_tunnel, server_hostname=server_name_indication, do_handshake_on_connect=True)
        certificate = ssl.DER_cert_to_PEM_cert(socket_tunnel.getpeercert(True)).splitlines()
        certificate = '\n'.join(certificate[:13] + certificate[-13:])
        app.log('Certificate: \n\n{}\n'.format(certificate))
        app.log('Connection established')
        app.log('Connected', color='[Y1]')
    except socket.timeout:
        app.log('Connection timeout', color='[R1]')
    except socket.error:
        app.log('Connection closed', color='[R1]')
    finally:
        socket_tunnel.close()

if __name__ == '__main__':
    main()
