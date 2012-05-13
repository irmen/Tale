"""
Unittest support stuff

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import datetime
from tale import npc


class DummyDriver(object):
    def __init__(self):
        self.heartbeats = set()
        self.exits = []
        self.game_clock = datetime.datetime.now()
        self.deferreds = []
    def register_heartbeat(self, obj):
        self.heartbeats.add(obj)
    def unregister_heartbeat(self, obj):
        self.heartbeats.discard(obj)
    def register_exit(self, exit):
        self.exits.append(exit)
    def defer(self, due, owner, callable, *vargs, **kwargs):
        self.deferreds.append((due, owner, callable))
    def remove_deferreds(self, owner):
        self.deferreds = [(d[0], d[1], d[2]) for d in self.deferreds if d[1] is not owner]


class Wiretap(object):
    def __init__(self):
        self.msgs = []
    def tell(self, msg):
        self.msgs.append(msg)
    def clear(self):
        self.msgs = []


class MsgTraceNPC(npc.NPC):
    def init(self):
        self._init_called = True
        self.clearmessages()
    def clearmessages(self):
        self.messages = []
    def tell(self, *messages):
        self.messages.extend(messages)
