import os
import re
import sys
import time
import queue
import socket
import requests
import threading

lock = threading.RLock(); os.system('clear'); 

timeouts = 0

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

def log(host, hostname, code, length, title, color='[W1]'):
    value = colors('{}{:<15}  {:<64}  {:<4}  {:<6}  {}[W2]'.format(color, host, hostname, code, length, title))
    with lock: print(value)

def log_replace(value):
    with lock:
        sys.stdout.write('{}      \r'.format(value))
        sys.stdout.flush()

log('host',            'hostname',                                                         'code', 'length', 'title')
log('---------------', '----------------------------------------------------------------', '----', '------', '-----')

class host_response_scanner(threading.Thread):
    def __init__(self, queue_host, queue_host_total):
        super(host_response_scanner, self).__init__()

        self.queue_host = queue_host
        self.queue_host_total = queue_host_total
        self.daemon = True

    def log(self, host, port, code, length, title, color):
        log(host, port, code, length, title, color=color)

    def log_replace(self, value):
        log_replace(value)

    def run(self):
        while True:
            time.sleep(0.250)
            self.scan(self.queue_host.get())
            self.queue_host.task_done()

    def scan(self, host):
        try:
            global timeouts
            self.tmp = host
            response = requests.get('http://{}'.format(host), timeout=5, allow_redirects=False)
            response_code = response.status_code
            response_title = re.findall(r'<title>(.*)</title>', response.text, re.IGNORECASE)
            response_title = response_title[0]  if len(response_title) else ''
            response_length = len(response.text) if len(response.text) else ''

            if response_code == 302 and response_length in [14, 22]:
                raise requests.exceptions.Timeout

            hostname, alias, ip = socket.gethostbyaddr(host)

            self.log(host, hostname, response_code, response_length, response_title, color='[G1]' if response_code == 400 else '[W1]')
        except socket.herror:
            self.log(host, '', response_code, response_length, response_title, color='[G1]' if response_code == 400 else '[W1]')
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            timeouts += 1
        finally:
            self.log_replace('({}/{}) ({}) ({})'.format(self.queue_host_total - self.queue_host.qsize(), self.queue_host_total, timeouts, self.tmp))


queue_host = queue.Queue()
threads = 64

ip_0 = sys.argv[1].split('.')
ip_0_0 = [0, 256]
ip_0_1 = [0, 256]
ip_0_2 = [0, 256]
ip_0_3 = [0, 255]

if len(ip_0) >= 1 and len(ip_0[0].strip()): ip_0_0 = [int(ip_0[0])]
if len(ip_0) >= 2 and len(ip_0[1].strip()): ip_0_1 = [int(ip_0[1])]
if len(ip_0) >= 3 and len(ip_0[2].strip()): ip_0_2 = [int(ip_0[2])]
if len(ip_0) >= 4 and len(ip_0[3].strip()): ip_0_3 = [int(ip_0[3])]

ip_1 = sys.argv[2].split('.') if len(sys.argv) >= 3 else sys.argv[1].split('.')
ip_0_0.append(int(ip_1[0]) + 1 if len(ip_1) >= 1 and len(ip_1[0].strip()) else (ip_0_0[0] + 1) if ip_0_0[0] else 256)
ip_0_1.append(int(ip_1[1]) + 1 if len(ip_1) >= 2 and len(ip_1[1].strip()) else (ip_0_1[0] + 1) if ip_0_1[0] else 256)
ip_0_2.append(int(ip_1[2]) + 1 if len(ip_1) >= 3 and len(ip_1[2].strip()) else (ip_0_2[0] + 1) if ip_0_2[0] else 256)
ip_0_3.append(int(ip_1[3]) + 1 if len(ip_1) >= 4 and len(ip_1[3].strip()) else (ip_0_3[0] + 1) if ip_0_3[0] else 255)

for a in range(ip_0_0[0], ip_0_0[1]):
    for b in range(ip_0_1[0], ip_0_1[1]):
        for c in range(ip_0_2[0], ip_0_2[1]):
            for d in range(ip_0_3[0], ip_0_3[1]):
                queue_host.put('{}.{}.{}.{}'.format(a, b, c, d))

queue_host_total = queue_host.qsize()

for i in range(threads if queue_host.qsize() >= threads else queue_host.qsize()):
    host_response_scanner(queue_host, queue_host_total).start()
    time.sleep(0.075)

queue_host.join(); print(' ' * 48)
