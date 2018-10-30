import asyncio
import pickle
from json import JSONDecodeError

from aiohttp import ClientSession as Client, WSMsgType

from ..net import get_host_ip
from ..settings import MASTER, MASTER_PORT
from ..util import uid, singleton, readonly
from .worker import WorkerManager


@singleton
class Slave:

    def __init__(self, _id=uid('Slave')):
        self.__worker_manager: WorkerManager = WorkerManager()
        # properties
        readonly(self, 'id', lambda: _id)
        readonly(self, 'result', lambda: self.__worker_manager.result)

    def start(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__handler())
        loop.close()

    async def __handler(self):
        async with Client().ws_connect('ws://%s:%s/master/' % (MASTER, MASTER_PORT)) as ws:
            # send init request
            init_data, data = {
                'command': 'init',
                'slave': get_host_ip()
            }, None
            await ws.send_json(init_data)
            # loop messages from master
            async for msg in ws:
                # handle exceptions
                if msg.type != WSMsgType.TEXT:
                    await ws.send_json({
                        'command': 'error',
                        'message': 'wrong message type'
                    })
                    continue
                try:
                    data = msg.json()
                except (TypeError, JSONDecodeError):
                    await ws.send_json({
                        'command': 'error',
                        'message': 'wrong json format'
                    })
                    continue

                assert 'command' in data
                # init command
                if 'init' == data['command']:
                    assert 'jobs' in data
                    for job_bytes in data['jobs']:
                        job = pickle.loads(bytes(job_bytes))
                        self.__worker_manager.dispatch(job)
                    # start testing
                    self.__worker_manager.start()
                elif 'stop' == data['command']:
                    self.__worker_manager.stop()
                    report_data = {
                        'command': 'report',
                        'result': self.__worker_manager.result.json_result
                    }
                    await ws.send_json(report_data)
                    break
