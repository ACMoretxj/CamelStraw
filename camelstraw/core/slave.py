from asyncio import get_event_loop

import dill
from aiohttp import ClientSession as Client, WSMsgType

from .job import JobContainer
from ..net import get_host_ip
from ..settings import MASTER, MASTER_PORT
from ..util import uid, singleton, readonly
from .worker import WorkerManager


@singleton
class Slave:

    def __init__(self, _id=uid('Slave')):
        self.__worker_manager = WorkerManager()
        # properties
        readonly(self, 'id', lambda: _id)
        readonly(self, 'result', lambda: self.__worker_manager.result)

    def start(self):
        loop = get_event_loop()
        loop.run_until_complete(self.__handler())
        loop.close()

    def __start(self):
        self.__worker_manager.start()

    def __stop(self):
        self.__worker_manager.stop()

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
                    self.__start()
                elif 'stop' == data['command']:
                    self.__stop()
                    report_data = {
                        'command': 'report',
                        'slave': get_host_ip(),
                        'result': self.result.json_result
                    }
                    await ws.send_json(report_data)
                    break
