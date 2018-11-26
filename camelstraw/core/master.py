from asyncio import get_event_loop, ensure_future, gather
from multiprocessing import Process
from typing import List

import dill
from aiohttp import web, ClientSession as Client, WSMsgType
from aiohttp.web_app import Application

from .slave import Slave
from .job import JobContainer
from .interfaces import AnalyseResult
from ..settings import SLAVES, MASTER_PORT, MASTER
from ..util import singleton, readonly


@singleton
class MasterService:
    """
    global controller
    """
    def __init__(self, jobs, worker_num=None, host='0.0.0.0', port=MASTER_PORT):
        self.__app = Application()
        self.__master = None
        self.__slaves = {}
        self.__results = {}
        # properties
        readonly(self, 'jobs', lambda: jobs)
        readonly(self, 'worker_num', lambda: worker_num)
        readonly(self, 'host', lambda: host)
        readonly(self, 'port', lambda: port)
        readonly(self, 'result', lambda: self.__results.get('master', None))

    def start(self):
        # execute websocket server in another process
        self.__app.add_routes([
            # communicate with slaves
            web.get('/slave/', self.__slave_handler),
            # communicate with master
            web.get('/master/', self.__master_handler)
        ])
        web.run_app(self.__app, host=self.host, port=self.port)

    async def __init_slave(self, slave, jobs, worker_num):
        ws = self.__slaves[slave]
        await ws.send_json({
            'command': 'init',
            'worker_num': worker_num,
            'jobs': [list(dill.dumps(job)) for job in jobs]
        })

    def __init_slaves(self):
        tasks, job_groups = [], [[] for _ in range(len(self.__slaves))]
        for i, job in enumerate(self.jobs):
            job_groups[i % len(self.__slaves)].append(job)
        for i, slave in enumerate(self.__slaves.keys()):
            tasks.append(self.__init_slave(slave, job_groups[i], self.worker_num))
        ensure_future(gather(*tasks))

    async def __stop_slave(self, slave):
        ws = self.__slaves[slave]
        await ws.send_json({
            'command': 'stop'
        })

    def __stop_slaves(self):
        tasks = [self.__stop_slave(slave) for slave in self.__slaves]
        ensure_future(gather(*tasks))

    async def __gather_result(self):
        if 'master' in self.__results:
            return
        self.__results['master'] = AnalyseResult\
            .from_results('master', list(self.__results.values()))
        # send data to master
        await self.__master.send_json({
            'command': 'report',
            'result': self.result.json_result
        })

    async def __slave_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        async for msg in ws:
            assert msg.type == WSMsgType.TEXT
            data = msg.json()
            assert 'command' in data and 'slave' in data
            # init command
            if 'init' == data['command']:
                # record the websocket
                self.__slaves[data['slave']] = ws
                # collected all the slave websockets
                if len(self.__slaves) >= len(SLAVES):
                    self.__init_slaves()
            # report command
            elif 'report' == data['command']:
                assert 'result' in data
                result = AnalyseResult.from_json(data['result'])
                self.__results[data['slave']] = result
                # collected all the results
                if len(self.__results) >= len(SLAVES):
                    await self.__gather_result()
        return ws

    async def __master_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        async for msg in ws:
            assert msg.type == WSMsgType.TEXT
            data = msg.json()
            assert 'command' in data
            if 'stop' == data['command']:
                self.__master = ws
                self.__stop_slaves()
        return ws


def start_service(jobs_bytes, worker_num):
    jobs: List[JobContainer] = dill.loads(jobs_bytes)
    service: MasterService = MasterService(jobs=jobs, worker_num=worker_num)
    service.start()


@singleton
class Master:

    def __init__(self, *jobs, worker_num=None):
        self.__process = None
        self.__jobs = list(jobs)
        self.__result = None
        # properties
        readonly(self, 'jobs', lambda: self.__jobs)
        readonly(self, 'result', lambda: self.__result)
        readonly(self, 'worker_num', lambda: worker_num)

    def start(self, local_mode=True):
        self.__process = Process(target=start_service, args=(
            dill.dumps(self.jobs), self.worker_num))
        self.__process.start()
        if local_mode:
            slave = Slave()
            slave.start()

    def stop(self):
        loop = get_event_loop()
        loop.run_until_complete(self.__stop())
        loop.close()
        self.__process.terminate()

    async def __stop(self):
        async with Client().ws_connect('ws://%s:%s/master/' % (MASTER, MASTER_PORT)) as ws:
            # send stop request
            await ws.send_json({'command': 'stop'})
            # receive result
            data = await ws.receive_json()
            assert 'command' in data and 'report' == data['command']
            assert 'result' in data
            self.__result = AnalyseResult.from_json(data['result'])
