import socket
from functools import lru_cache


@lru_cache()
def get_host_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as skt:
        skt.connect(('8.8.8.8', 80))
        ip = skt.getsockname()[0]
        return ip
