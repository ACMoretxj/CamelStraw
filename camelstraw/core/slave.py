from asyncio import get_event_loop, new_event_loop, set_event_loop
from multiprocessing import Process

import dill
from aiohttp import ClientSession as Client, WSMsgType

from .job import JobContainer
from ..net import get_host_ip
from ..settings import MASTER, MASTER_PORT
from ..util import uid, singleton, readonly
from .worker import WorkerManager


@singleton
class SlaveService:
    """
    Synchronize operations extracted from Slave, for the purpose
    that main program can interact with slave without being blocked
    """
    def __init__(self, _id=uid('Slave-Service')):
        self.__worker_manager = WorkerManager()
        # properties
        readonly(self, 'id', lambda: _id)
        readonly(self, 'result', lambda: self.__worker_manager.result)

    def start(self):
        loop = get_event_loop()
        loop.run_until_complete(self.__handler())
        loop.close()

    async def __handler(self):
        async with Client().ws_connect('ws://%s:%s/slave/' % (MASTER, MASTER_PORT)) as ws:
            # send init request
            await ws.send_json({
                'command': 'init',
                'slave': get_host_ip()
            })
            # loop messages from master
            async for msg in ws:
                # handle exceptions
                assert msg.type == WSMsgType.TEXT
                data = msg.json()
                assert 'command' in data
                # init command
                if 'init' == data['command']:
                    assert 'jobs' in data
                    for job_bytes in data['jobs']:
                        job: JobContainer = dill.loads(bytes(job_bytes))
                        self.__worker_manager.dispatch(job)
                    self.__worker_manager.start()
                elif 'stop' == data['command']:
                    self.__worker_manager.stop()
                    report_data = {
                        'command': 'report',
                        'slave': get_host_ip(),
                        'result': self.result.json_result
                    }
                    await ws.send_json(report_data)
                    break


def start_service():
    service = SlaveService()
    service.start()


@singleton
class Slave:

    def __init__(self, _id=uid('Slave')):
        self.__process = None
        # properties
        readonly(self, 'id', lambda: _id)

    def start(self):
        self.__process = Process(target=start_service)
        self.__process.start()
