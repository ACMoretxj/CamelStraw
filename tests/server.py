from hashlib import sha256

import time
from random import random

from aiohttp import web, WSMsgType
from aiohttp.web_request import Request

from camelstraw.util import singleton


async def http_handler(request: Request):
    content = request.query_string
    if request.method == 'POST':
        content = await request.text()
    resp = sha256(('%s-%s-%s' % (content, time.time(), random())).encode()).hexdigest()
    return web.Response(text=resp)


async def websocket_handler(request: Request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    async for msg in ws:
        resp = 'wrong message type'
        if msg.type == WSMsgType.TEXT:
            resp = sha256(('%s-%s-%s' % (msg.data, time.time(), random())).encode()).hexdigest()
        elif msg.type == WSMsgType.BINARY:
            resp = sha256(msg.data + ('%s-%s' % (time.time(), random())).encode()).hexdigest()
        await ws.send_str(resp)
    return ws


@singleton
class TestServer:

    def __init__(self):
        self.__app = web.Application()
        self.__app.add_routes([
            web.get('/http/get/', http_handler),
            web.post('/http/post/', http_handler),
            web.get('/ws/text/', websocket_handler),
            web.get('/ws/binary/', websocket_handler)
        ])

    def run(self, host='localhost', port=8000):
        web.run_app(self.__app, host=host, port=port)
