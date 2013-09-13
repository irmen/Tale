"""
Threading primitives.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

try:
    import threading
    has_threads = True
except ImportError:
    import dummy_threading as threading
    has_threads = False
    # Even with dummy threading, you can still play stories
    # that have server_tick_method=command.
    # Server_tick_method=timer (async) won't work though.


Event = threading.Event
Lock = threading.Lock
Thread = threading.Thread
local = threading.local
active_count = threading.active_count
