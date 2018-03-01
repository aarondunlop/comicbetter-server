#!/usr/bin/env python3

import logging
import socket
import sys
from time import sleep
import socket
import requests

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def get_fqdn():
    r = requests.get('https://localhost/getfqdn', verify=False)
    r.status_code
    print(r.text)
    return r.text

from zeroconf import ServiceInfo, Zeroconf

if __name__ == '__main__':
    get_fqdn()
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) > 1:
        assert sys.argv[1:] == ['--debug']
        logging.getLogger('zeroconf').setLevel(logging.DEBUG)

    details = {'uri': get_fqdn(), 'server': 'Comicbetter'}

    info = ServiceInfo('_http._tcp.local.',
                      'CBServer._http._tcp.local.',
                       socket.inet_aton(get_ip()), 443, 0, 0,
                       details)

    zeroconf = Zeroconf()
    zeroconf.register_service(info)

    try:
        while True:
            sleep(0.1)
    finally:
        zeroconf.unregister_service(info)
        zeroconf.close()
