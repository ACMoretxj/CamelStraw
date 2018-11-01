import multiprocessing
import time
from multiprocessing import Process

from camelstraw import HttpGetJob, Slave, HttpPostJob, WebsocketTextJob, WebsocketBinaryJob
from camelstraw.core.master import Master
from tests.server import TestServer


def start_server():
    server = TestServer()
    server.run()


def start_master():
    def callback(status_code, content):
        # print(multiprocessing.current_process().name, status_code, content)
        pass

    jobs = (
        HttpGetJob('http://localhost:8000/http/get/?wxid=acmore', callback=callback, reuse_job=False),
        HttpPostJob('http://localhost:8000/http/post/', data={'wxid': 'acmore'}, callback=callback, reuse_job=False),
        WebsocketTextJob('ws://localhost:8000/ws/text/', data='acmore', callback=callback, reuse_job=False),
        WebsocketBinaryJob('ws://localhost:8000/ws/binary/', data=b'acmore', callback=callback, reuse_job=False),
    )
    master = Master()
    master.dispatch(*jobs)
    master.start()
    time.sleep(100)
    master.stop()
    print(master.result)


def start_slave():
    slave = Slave()
    slave.start()


if __name__ == '__main__':
    # start test server
    server_process = Process(target=start_server)
    server_process.start()

    # start master
    master_process = Process(target=start_master)
    master_process.start()

    # start slave
    slave_process = Process(target=start_slave)
    slave_process.start()

    # stop processes
    # slave_process.terminate()
    # server_process.terminate()
    # master_process.terminate()
