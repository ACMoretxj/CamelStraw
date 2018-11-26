import time
from multiprocessing import Process, current_process
from os import cpu_count

from camelstraw import HttpGetJob, HttpPostJob, WebsocketTextJob, WebsocketBinaryJob, Launcher
from tests.server import TestServer


def start_server():
    server = TestServer()
    server.run()


def start_launcher():

    def callback(status_code, content):
        print(current_process().name, status_code, content)

    jobs = (
        HttpGetJob('http://localhost:8000/http/get/?wxid=acmore', callback=callback, reuse_job=False),
        HttpPostJob('http://localhost:8000/http/post/', data={'wxid': 'acmore'}, callback=callback, reuse_job=False),
        WebsocketTextJob('ws://localhost:8000/ws/text/', data='acmore', callback=callback, reuse_job=False),
        WebsocketBinaryJob('ws://localhost:8000/ws/binary/', data=b'acmore', callback=callback, reuse_job=False),
    )

    launcher = Launcher(*jobs, duration=10, worker_num=1)
    launcher.launch()


if __name__ == '__main__':
    # start test server
    server_process = Process(target=start_server)
    server_process.start()

    # launcher master
    launcher_process = Process(target=start_launcher)
    launcher_process.start()
