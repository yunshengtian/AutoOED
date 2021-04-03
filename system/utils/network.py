import ipaddress
import requests
import socket


def get_public_ip():
    try:
        public_ip = requests.get('https://checkip.amazonaws.com').text.strip()
    except:
        public_ip = 'unknown'
    return public_ip


def get_internal_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        internal_ip = s.getsockname()[0]
    except:
        internal_ip = 'unknown'
    return internal_ip