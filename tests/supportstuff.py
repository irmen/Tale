"""
Unittest support stuff

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import datetime
from tale import npc
from tale import pubsub
from tale import util


class DummyDriver(object):
    def __init__(self):
        self.heartbeats = set()
        self.exits = []
        self.game_clock = util.GameDateTime(datetime.datetime.now())
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

    def get_current_verbs(self):
        return {}


class Wiretap(pubsub.Listener):
    def __init__(self, target):
        self.clear()
        tap = target.get_wiretap()
        tap.subscribe(self)

    def pubsub_event(self, topicname, event):
        sender, message = event
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
