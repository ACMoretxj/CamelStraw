import socket


def get_host_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as skt:
        skt.connect(('8.8.8.8', 80))
        ip = skt.getsockname()[0]
        return ip
