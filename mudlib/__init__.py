"""
The actual mudlib 'world' code

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import threading

_threadlocal = threading.local()


class __MudContextProxy(object):
    def __getattr__(self, item):
        ctx = getattr(_threadlocal, "mud_context", None)
        if ctx is None:
            ctx = _threadlocal.mud_context = {}
        return ctx[item]

    def __setattr__(self, key, value):
        ctx = getattr(_threadlocal, "mud_context", None)
        if ctx is None:
            ctx = _threadlocal.mud_context = {}
        ctx[key] = value


mud_context = __MudContextProxy()
