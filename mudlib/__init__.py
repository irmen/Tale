"""
The actual mudlib 'world' code

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import threading

MUD_NAME = "Snakepit"
MUD_BANNER = r"""
  ___              _          ___  _  _
 / __| _ _   __ _ | |__ ___  | _ \(_)| |_
 \__ \| ' \ / _` || / // -_) |  _/| ||  _|  by Irmen de Jong
 |___/|_||_|\__,_||_\_\\___| |_|  |_| \__|  irmen@razorvine.net
"""


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
