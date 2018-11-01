import asyncio
from multiprocessing import Process
from typing import List

import dill
from aiohttp import web, ClientSession as Client, WSMsgType
from aiohttp.web_app import Application

from camelstraw.core.job import JobContainer
from .interfaces import AnalyseResult
from ..settings import SLAVES, MASTER_PORT, MASTER
from ..util import singleton, readonly


@singleton
class MasterService:
    """
    global controller
    """
    def __init__(self, jobs, host='0.0.0.0', port=MASTER_PORT):
        self.__app = Application()
        self.__master = None
        self.__slaves = {}
        self.__results = {}
        # properties
        readonly(self, 'jobs', lambda: jobs),
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

    async def __init_slave(self, slave, jobs):
        ws = self.__slaves[slave]
        data = {
            'command': 'init',
            'jobs': [list(dill.dumps(job)) for job in jobs]
        }
        await ws.send_json(data)

    def __init_slaves(self):
        tasks, job_groups = [], [[] for _ in range(len(self.__slaves))]
        for i, job in enumerate(self.jobs):
            job_groups[i % len(self.__slaves)].append(job)
        for i, slave in enumerate(self.__slaves.keys()):
            tasks.append(self.__init_slave(slave, job_groups[i]))
        asyncio.ensure_future(asyncio.gather(*tasks))

    async def __stop_slave(self, slave):
        ws = self.__slaves[slave]
        data = {'command': 'stop'}
        await ws.send_json(data)

    def __stop_slaves(self):
        tasks = [self.__stop_slave(slave) for slave in self.__slaves]
        asyncio.ensure_future(asyncio.gather(*tasks))

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


def start_service(jobs_bytes):
    jobs: List[JobContainer] = dill.loads(jobs_bytes)
    service: MasterService = MasterService(jobs=jobs)
    service.start()


@singleton
class Master:

    def __init__(self):
        self.__process = None
        self.__jobs = []
        self.__result = None
        # properties
        readonly(self, 'result', lambda: self.__result)

    def dispatch(self, *jobs):
        self.__jobs.extend(jobs)

    def start(self):
        self.__process = Process(target=start_service, args=(dill.dumps(self.__jobs),))
        self.__process.start()

    def stop(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__stop())
        loop.close()
        self.__process.terminate()

    async def __stop(self):
        async with Client().ws_connect('ws://%s:%s/master/' % (MASTER, MASTER_PORT)) as ws:
            # send stop request
            await ws.send_json({'command': 'stop'})
            # receive result
            data = await ws.receive_json()
            assert 'command' in data
            assert 'report' == data['command']
            assert 'result' in data
            self.__result = AnalyseResult.from_json(data['result'])
