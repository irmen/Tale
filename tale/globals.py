"""
Global context object (thread-safe) for the server

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import threading
import datetime

_threadlocal = threading.local()


class __MudContextProxy(object):
    def __getattr__(self, item):
        ctx = getattr(_threadlocal, "mud_context", None)
        if ctx is None:
            ctx = _threadlocal.mud_context = {}
        return ctx.get(item)

    def __setattr__(self, key, value):
        ctx = getattr(_threadlocal, "mud_context", None)
        if ctx is None:
            ctx = _threadlocal.mud_context = {}
        ctx[key] = value


mud_context = __MudContextProxy()

MAX_SCORE = 100     # arbitrary, but when max score is reached, the game is supposed to end. Use 0 or None to disable scoring.
SERVER_TICK_METHOD = "timer"    # 'command' (waits for player entry) or 'timer' (async timer driven)
SERVER_TICK_TIME = 1.0    # time between server ticks (in seconds) (usually 1.0 for 'timer' tick method)
GAMETIME_TO_REALTIME = 5    # meaning: game time is X times the speed of real time (only used with "timer" tick method)
GAMETIME_EPOCH = datetime.datetime(2012, 4, 19, 14, 0, 0)    # start date/time of the game clock
DISPLAY_GAMETIME = True    # enable/disable display of the game time at certain moments

GAME_TITLE = "Snakepit"
GAME_VERSION = "0.3"    # arbitrary but should be changed when the game code or any parameter here is changed
REQUIRES_TALE_VERSION = "0.3"    # tale library required to run the game
