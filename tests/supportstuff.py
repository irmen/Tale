"""
Unittest support stuff

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division, unicode_literals
import datetime
import blinker
from tale import npc


class DummyDriver(object):
    def __init__(self):
        self.heartbeats = set()
        self.exits = []
        self.game_clock = datetime.datetime.now()
        self.deferreds = []
        self.after_player_queue = []
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
    def after_player_action(self, callable, *vargs, **kwargs):
        self.after_player_queue.append((callable, vargs, kwargs))
    def execute_after_player_actions(self):
        for callable, vargs, kwargs in self.after_player_queue:
            callable(*vargs, **kwargs)
        self.after_player_queue = []


class Wiretap(object):
    def __init__(self):
        self.clear()
        tap = blinker.signal("wiretap")
        tap.connect(self.tell)
    def tell(self, sender, message):
        self.msgs.append((sender, message))
        self.senders.append(sender)
    def clear(self):
        self.msgs = []
        self.senders = []


class MsgTraceNPC(npc.NPC):
    def init(self):
        self._init_called = True
        self.clearmessages()
    def clearmessages(self):
        self.messages = []
    def tell(self, *messages):
        self.messages.extend(messages)
