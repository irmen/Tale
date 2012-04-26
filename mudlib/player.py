"""
Player code

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division
import sys
if sys.version_info < (3, 0):
    import Queue as queue
else:
    import queue
from threading import Event
import time
from . import base, soul
from . import lang
from .errors import SecurityViolation, ActionRefused


class Player(base.Living):
    """
    Player controlled entity.
    Has a Soul for social interaction.
    """
    def __init__(self, name, gender, race="human", description=None):
        title = lang.capital(name)
        super(Player, self).__init__(name, gender, title, description, race)
        self.soul = soul.Soul()
        self._output = []
        self.score = 0
        self.turns = 0
        self.init_nonserializables()

    def init_nonserializables(self):
        self.installed_wiretaps = set()
        self._input = queue.Queue()
        self.input_is_available = Event()
        self.transcript = None

    def __repr__(self):
        return "<%s.%s '%s' @ 0x%x, privs:%s>" % (self.__class__.__module__, self.__class__.__name__,
            self.name, id(self), ",".join(self.privileges) or "-")

    def __getstate__(self):
        state = super(Player, self).__getstate__()
        # skip all non-serializable things
        del state["installed_wiretaps"]
        del state["_input"]
        del state["input_is_available"]
        del state["transcript"]
        return state

    def __setstate__(self, state):
        super(Player, self).__setstate__(state)
        self.init_nonserializables()

    def set_title(self, title, includes_name_param=False):
        if includes_name_param:
            self.title = title % lang.capital(self.name)
        else:
            self.title = title

    def parse(self, commandline, external_verbs=frozenset(), room_exits=None):
        """Parse the commandline into something that can be processed by the soul (soul.ParseResult)"""
        parsed = self.soul.parse(self, commandline, external_verbs, room_exits)
        if external_verbs and parsed.verb in external_verbs:
            raise soul.NonSoulVerb(parsed)
        if parsed.verb not in soul.NONLIVING_OK_VERBS:
            # check if any of the targeted objects is a non-living
            if not all(isinstance(who, base.Living) for who in parsed.who):
                raise soul.NonSoulVerb(parsed)
        return parsed

    def socialize_parsed(self, parsed):
        """Don't re-parse the command string, but directly feed the parse results we've already got into the Soul"""
        return self.soul.process_verb_parsed(self, parsed)

    def tell(self, *messages):
        """
        A message sent to a player (or multiple messages). They are meant to be printed on the screen.
        For efficiency, messages are gathered in a buffer and printed later.
        Notice that the signature and behavior of this method resembles that of the print() function,
        which means you can easily do: print=player.tell, and use print(..) everywhere as usual.
        """
        super(Player, self).tell(*messages)
        self._output.append(" ".join(str(msg) for msg in messages))
        self._output.append("\n")

    def get_output_lines(self):
        """gets the accumulated output lines and clears the buffer"""
        lines = self._output
        self._output = []
        if self.transcript:
            self.transcript.writelines(lines)
        return lines

    def look(self, short=False):
        """look around in your surroundings (exclude player from livings)"""
        if self.location:
            look = self.location.look(exclude_living=self, short=short)
            if "wizard" in self.privileges:
                return repr(self.location) + "\n" + look
            return look
        else:
            return "You see nothing."

    def create_wiretap(self, target):
        if "wizard" not in self.privileges:
            raise SecurityViolation("wiretap requires wizard privilege")
        tap = Wiretap(self, target)
        self.installed_wiretaps.add(tap)  # hold on to the wiretap otherwise it's garbage collected immediately
        target.wiretaps.add(tap)  # install the wiretap on the target

    def destroy(self, ctx):
        self.activate_transcript(False)
        super(Player, self).destroy(ctx)
        self.installed_wiretaps.clear()  # the references from within the observed are cleared by means of weakrefs
        self.soul = None   # truly die ;-)
        # @todo: remove deferreds, etc.

    def allow_give_money(self, actor, amount):
        """Do we accept money?"""
        pass

    def get_pending_input(self):
        result = []
        self.input_is_available.clear()
        try:
            while True:
                result.append(self._input.get_nowait())
        except queue.Empty:
            return result

    def input(self, cmd):
        self._input.put(cmd)
        if self.transcript:
            self.transcript.write("\n>> %s\n\n" % cmd)
        self.input_is_available.set()
        self.turns += 1

    def activate_transcript(self, file):
        if file:
            if self.transcript:
                raise ActionRefused("There's already a transcript being made to " + self.transcript.name)
            self.transcript = open(file, "a")
            self.transcript.write("\n*Transcript starting at %s*\n\n" % time.ctime())
            self.tell("Transcript is being written to", file)
        else:
            if self.transcript:
                self.transcript.write("\n*Transcript ending at %s*\n\n" % time.ctime())
                self.transcript.close()
                self.transcript = None
            self.tell("Transcript ended.")


class Wiretap(object):
    """wiretap that can be installed on a location or a living, to tap into the messages they're receiving"""
    def __init__(self, observer, target):
        self.observer = observer
        self.target_name = target.name
        self.target_type = target.__class__.__name__

    def __str__(self):
        return "%s '%s'" % (self.target_type, self.target_name)

    def tell(self, *messages):
        for msg in messages:
            self.observer.tell("[wiretap on '%s': %s]" % (self.target_name, msg))
