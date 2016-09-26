#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

'''
async web application.
'''

import logging; logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web  # 类似于flask，是HTTP框架

def index(request):
    return web.Response(body=b'<h1>Awesome</h1>')

async def init(loop):
    app = web.Application(loop=loop)  # 和flask的Flask()类似
    app.router.add_route('GET', '/', index)  # 为应用绑定路径和方法以及处理函数
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)  # 设置端口服务，应用上面的绑定
    print(srv)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
