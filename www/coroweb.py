#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""web框架"""

__author__ = 'Michael Liao'

import asyncio, os, inspect, logging, functools

from urllib import parse

from aiohttp import web

from apis import APIError

def get(path):
    '''
    Define decorator @get('/path')
    '''
    def decorator(func):
        # 这个是用来处理被装饰函数签名的
        # 比如__name__还有下面的__method__
        @functools.wraps(func)
        # 两层装饰器是为了加参数，比如@get('/path')
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator

def post(path):
    '''
    Define decorator @post('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator

# 获取函数的值为空的命名关键字参数
def get_required_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters  # 查看函数签名，把参数列表在params里面
    for name, param in params.items():
        # KEYWORD_ONLY表示命名关键字参数
        # 判断参数是不是只有命名关键字参数并且默认值为空
        # 为了获得必须要填写的参数
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)

# 获取命名关键字参数
def get_named_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        # 为了获得所有的命名关键字参数
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)

# 判断是否有命名关键字参数
def has_named_kw_args(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True

# 判断是否有关键字参数
def has_var_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        # VAR_KEYWORD表示关键字参数，匹配**kw
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True

# 判断参数里面是不是有请求关键字        
def has_request_arg(fn):
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        if name == 'request':
            found = True
            continue # 这里跳出本次循环是因为请求参数必须是最后一个，提前跳出就会报错
        # VAR_POSITIONAL表示可选参数，匹配*args
        if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            raise ValueError('request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
    return found

# 这个RQ是用来封装http处理函数的
# 1.接收并分析url函数所需要的参数
# 2.分析http method, content type并做出相应处理
# 3.把参数封装到kw中作为self._func(**kw)参数
# 另外关于kw的参数
# request.match_info的参数： match_info主要是保存像@get('/blog/{id}')里面的id，就是路由路径里的参数
# GET的参数： 像例如/?page=2
# POST的参数： api的json或者是网页中from
# request参数： 有时需要验证用户信息就需要获取request里面的数据
# 详情见day5下面的评论
class RequestHandler(object):

    def __init__(self, app, fn):
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)

    # __call__()方法是为了让他的实例为函数，比如RequestHandler(app, fn)就相当于调用了函数
    # request是前端发过来的
    async def __call__(self, request):
        kw = None
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            if request.method == 'POST':
                if not request.content_type:
                    return web.HTTPBadRequest('Missing Content-Type.')
                ct = request.content_type.lower()
                # startswith() 方法用于检查字符串是否是以指定子字符串开头
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest('JSON body must be object.')
                    kw = params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)
            if request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k, v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]
        if kw is None:
            # match_info主要是保存像@get('/blog/{id}')里面的id，就是路由路径里的参数
            kw = dict(**request.match_info)
        else:
            if not self._has_var_kw_arg and self._named_kw_args:
                # remove all unamed kw:
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            # check named arg:
            for k, v in request.match_info.items():
                if k in kw:
                    logging.warning('Duplicate arg name in named arg and kw args: %s' % k)
                kw[k] = v
        if self._has_request_arg:
            kw['request'] = request
        # check required kw:
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest('Missing argument: %s' % name)
        logging.info('call with args: %s' % str(kw))
        try:
            r = await self._func(**kw)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)

# 注册静态文件
def add_static(app):
    # os.path.abspath返回绝对路径
    # os.path.dirname返回文件的目录的路径
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    # 告诉python静态文件储存的路径
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))

# 注册url函数
def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    # 把函数编程协程函数
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method, path, RequestHandler(app, fn))

# 一次性注册一个py文件里所有的url函数
def add_routes(app, module_name):
    # rfind() 返回字符串最后一次出现的位置，如果没有匹配项则返回-1
    # 比如handlers
    n = module_name.rfind('.')
    if n == (-1):
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n+1:]  # name是点后面的
        # 相当于from module_name[:n] import name
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    # dir(mod)就是这个模块里面的所有属性
    for attr in dir(mod):
        # 排除系统属性
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        # 如果可以调用
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)
