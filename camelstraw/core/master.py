import asyncio
import json
import pickle
from json import JSONDecodeError
from multiprocessing import Process
from typing import Dict, List

from aiohttp import web, WSMsgType
from aiohttp.web_request import Request

from .interfaces import AnalyseResult
from .job import JobContainer
from ..settings import SLAVES, MASTER_PORT
from ..util import singleton


@singleton
class MasterService:
    """
    websocket handler for the purpose of communicating with slaves
    """
    def __init__(self, jobs: List[JobContainer]):
        self.__slaves: Dict[str, web.WebSocketResponse] = {}
        self.__results: Dict[str, AnalyseResult] = {}
        self.__jobs: List[JobContainer] = jobs
        self.__app = web.Application()
        self.__app.add_routes([web.get('/master/', self.__handler)])
        # properties
        self.result = property(lambda: self.__results.get('master', None))

    def run(self, host='0.0.0.0', port=MASTER_PORT):
        # execute in another process
        process = Process(target=lambda: web.run_app(self.__app, host=host, port=port))
        process.start()

    async def __init_slave(self, slave: str, jobs: List[JobContainer]):
        ws = self.__slaves[slave]
        data = {
            'command': 'init',
            'jobs': [list(pickle.dumps(job)) for job in jobs]
        }
        await ws.send_json(data)

    def __init_slaves(self):
        tasks, job_groups = [], [[] for _ in range(len(self.__slaves))]
        for i, job in enumerate(self.__jobs):
            job_groups[i % len(self.__slaves)].append(job)
        for i, slave in enumerate(self.__slaves.keys()):
            tasks.append(self.__init_slave(slave, job_groups[i]))
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()

    def __gather_result(self):
        if 'master' in self.__results:
            return
        self.__results['master'] = AnalyseResult\
            .from_results('master', list(self.__results.values()))

    async def __handler(self, request: Request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                await ws.send_str('wrong message type')
                continue
            try:
                # recover data
                data = json.loads(msg.data)
                assert 'command' in data and 'slave' in data
                # init command
                if 'init' == data['command']:
                    # record the websocket
                    self.__slaves[data['slave']] = ws
                    # collected all the slaves
                    if len(self.__slaves) >= len(SLAVES):
                        self.__init_slaves()
                # report command
                elif 'report' == data['command']:
                    result = AnalyseResult.from_json(data)
                    self.__results[data['slave']] = result
                    # collected all the slaves
                    if len(self.__slaves) >= len(SLAVES):
                        self.__gather_result()
            except (TypeError, JSONDecodeError):
                await ws.send_str('wrong json format')
        return ws


@singleton
class Master:
    """
    global controller
    """
    def __init__(self):
        jobs = []
        self.__service = MasterService(jobs)

    def start(self):
        self.__service.run()

    def stop(self):
        pass
