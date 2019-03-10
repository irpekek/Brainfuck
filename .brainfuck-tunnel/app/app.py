import os
import shutil
import datetime
from threading import RLock

lock = RLock()

def real_path(file_name):
    return os.path.dirname(os.path.abspath(__file__)) + file_name

def colors(value):
    patterns = {
        'CC' : '\033[0m',    'BB' : '\033[1m',
        'D1' : '\033[30;1m', 'D2' : '\033[30;2m',
        'R1' : '\033[31;1m', 'R2' : '\033[31;2m',
        'G1' : '\033[32;1m', 'G2' : '\033[32;2m',
        'Y1' : '\033[33;1m', 'Y2' : '\033[33;2m',
        'B1' : '\033[34;1m', 'B2' : '\033[34;2m',
        'P1' : '\033[35;1m', 'P2' : '\033[35;2m',
        'C1' : '\033[36;1m', 'C2' : '\033[36;2m',
        'W1' : '\033[37;1m', 'W2' : '\033[37;2m'
    }

    for code in patterns:
        value = value.replace('[{}]'.format(code), patterns[code])

    return value

def log_file(file_name, value, color='[G1]'):
    with lock:
        with open(file_name, 'a') as file:
            file.write(colors('{color}[{time}] {value}\n'.format(
                time=datetime.datetime.now().strftime('%H:%M:%S'),
                value=value,
                color=color
            )))

def get_file_names():
    return [
        'config/config.json',
        'config/payload.txt',
        'config/proxies.txt',
        'config/server-name-indication.txt',
        'database/account.json'
    ]

def reset_to_default_settings():
    for file_name in get_file_names():
        try:
            os.remove(real_path('/../' + file_name))
        except: pass

    default_settings()

def default_settings():
    for file_name in get_file_names():
        try:
            open(real_path('/../' + file_name))
        except:
            shutil.copyfile(real_path('/default/' + file_name), real_path('/../' + file_name))
