#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Configuration
'''

__author__ = 'Michael Liao'

import config_default

class Dict(dict):
    '''
    Simple dict but support access as x.y style.
    '''
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

def merge(defaults, override):
    r = {}
    for k, v in defaults.items():
        # 如果重载内容中又相同的key
        if k in override:
            # 如果对应的值还是一个dict，就要再检查里面的内容是不是完全相同
            # 于是就重复上面的，也就是递归
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            # 不是的话就直接覆盖
            else:
                r[k] = override[k]
        # 另外的就还是按照默认的来
        else:
            r[k] = v
    return r

# 把dict变成可以有点运算的特殊dict
def toDict(d):
    D = Dict()
    for k, v in d.items():
        D[k] = toDict(v) if isinstance(v, dict) else v
    return D

configs = config_default.configs

try:
    import config_override
    configs = merge(configs, config_override.configs)
except ImportError:
    pass

configs = toDict(configs)
