import asyncio
import pickle
from json import JSONDecodeError

from aiohttp import web, WSMsgType
from aiohttp.web_app import Application

from .interfaces import AnalyseResult
from ..settings import SLAVES, MASTER_PORT
from ..util import singleton, readonly


@singleton
class Master:
    """
    global controller
    """
    def __init__(self, host='0.0.0.0', port=MASTER_PORT):
        self.__service = Application()
        self.__slaves = {}
        self.__results = {}
        self.__jobs = []
        # properties
        readonly(self, 'host', lambda: host)
        readonly(self, 'port', lambda: port)
        readonly(self, 'result', lambda: self.__results.get('master', None))

    def dispatch(self, *jobs):
        self.__jobs.extend(jobs)

    def start(self):
        # execute websocket server in another process
        self.__service.add_routes([web.get('/master/', self.__handler)])
        web.run_app(self.__service, host=self.host, port=self.port)

    def stop(self):
        tasks = [self.__stop_slave(slave) for slave in self.__slaves]
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()
        self.__service.shutdown()
        self.__service.cleanup()

    async def __init_slave(self, slave, jobs):
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

    async def __handler(self, request):
        ws, data = web.WebSocketResponse(), None
        await ws.prepare(request)
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
                    self.__gather_result()
        return ws

    async def __stop_slave(self, slave):
        ws = self.__slaves[slave]
        data = {'command': 'stop'}
        await ws.send_json(data)
