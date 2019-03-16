import os
import app
import json

def real_path(file_name):
    return os.path.dirname(os.path.abspath(__file__)) + file_name

def log_file(value, color='[G1]'):
    app.log_file(real_path('/storage/app.log'), value, color=color)

def main():
    with open(real_path('/storage/app.pid'), 'a') as file: file.write('{}\n'.format(os.getpid()))

    config = json.loads(open(real_path('/config/config.json')).read())
    inject_host = str(config['inject_host'])
    inject_port = int(config['inject_port'])
    tunnel_type = str(config['tunnel_type'])
    proxy_command = config['proxy_command']

    app.inject((inject_host, inject_port), tunnel_type).start()
    
    ssh_client = app.ssh_client((inject_host, inject_port), proxy_command)
    ssh_client.account = json.loads(open(real_path('/database/account.json')).read())
    ssh_client.start()

if __name__ == '__main__':
    main()
