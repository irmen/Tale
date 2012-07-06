"""
Player code

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division, unicode_literals
from threading import Event
import time
import textwrap
from . import base
from . import soul
from . import lang
from . import color
from . import textoutput
from . import hints
from .errors import SecurityViolation, ActionRefused, ParseError
from .util import queue


DEFAULT_SCREEN_WIDTH = 72
DEFAULT_SCREEN_INDENT = 2


class Player(base.Living):
    """
    Player controlled entity.
    Has a Soul for social interaction.
    """
    def __init__(self, name, gender, race="human", description=None, short_description=None):
        title = lang.capital(name)
        super(Player, self).__init__(name, gender, race, title, description, short_description)
        self.soul = soul.Soul()
        self.verbs = []   # things can add custom verbs to this list when they're in the player's inventory
        self.turns = 0
        self.state = {}
        self.hints = hints.HintSystem()
        self.previous_commandline = None
        self.screen_width = DEFAULT_SCREEN_WIDTH
        self.screen_indent = DEFAULT_SCREEN_INDENT
        self.brief = 0  # 0=off, 1=short descr. for known locations, 2=short descr. for all locations
        self.known_locations = set()
        self.story_complete = False
        self.story_complete_callback = None
        self.init_nonserializables()

    def init_nonserializables(self):
        self.installed_wiretaps = set()
        self._input = queue.Queue()
        self.input_is_available = Event()
        self.transcript = None
        indent = " " * self.screen_indent
        self.textwrapper = textwrap.TextWrapper(initial_indent=indent, subsequent_indent=indent,
                                                width=self.screen_width, fix_sentence_endings=True)
        self._output = textoutput.TextOutput(self.textwrapper)

    def __repr__(self):
        return "<%s '%s' @ 0x%x, privs:%s>" % (self.__class__.__name__,
            self.name, id(self), ",".join(self.privileges) or "-")

    def __getstate__(self):
        state = super(Player, self).__getstate__()
        # skip all non-serializable things (or things that need to be reinitialized)
        for name in ["installed_wiretaps", "_input", "_output", "input_is_available", "transcript", "textwrapper"]:
            del state[name]
        return state

    def __setstate__(self, state):
        super(Player, self).__setstate__(state)
        self.init_nonserializables()

    def set_screen_sizes(self, indent, width):
        self.screen_indent = indent
        self.screen_width = width
        self.textwrapper.initial_indent = self.textwrapper.subsequent_indent = " " * indent
        self.textwrapper.width = width

    def set_title(self, title, includes_name_param=False):
        if includes_name_param:
            self.title = title % lang.capital(self.name)
        else:
            self.title = title

    def story_completed(self, callback=None):
        """The player completed the story. Set some flags"""
        self.story_complete = True
        self.story_complete_callback = callback

    def parse(self, commandline, external_verbs=frozenset()):
        """Parse the commandline into something that can be processed by the soul (soul.ParseResult)"""
        if commandline == "again":
            # special case, repeat previous command
            if self.previous_commandline:
                commandline = self.previous_commandline
                self.tell(color.dim("(repeat: %s)" % commandline), end=True)
            else:
                raise ActionRefused("Can't repeat your previous action.")
        self.previous_commandline = commandline
        parsed = self.soul.parse(self, commandline, external_verbs)
        if external_verbs and parsed.verb in external_verbs:
            raise soul.NonSoulVerb(parsed)
        if parsed.verb not in soul.NONLIVING_OK_VERBS:
            # check if any of the targeted objects is a non-living
            if not all(isinstance(who, base.Living) for who in parsed.who_order):
                raise soul.NonSoulVerb(parsed)
        self.validate_socialize_targets(parsed)
        return parsed

    def validate_socialize_targets(self, parsed):
        """check if any of the targeted objects is an exit"""
        if any(isinstance(w, base.Exit) for w in parsed.who_info):
            raise ParseError("That doesn't make much sense.")

    def socialize_parsed(self, parsed):
        """Don't re-parse the command string, but directly feed the parse results we've already got into the Soul"""
        return self.soul.process_verb_parsed(self, parsed)

    def tell(self, *messages, **kwargs):
        """
        A message sent to a player (or multiple messages). They are meant to be printed on the screen.
        For efficiency, messages are gathered in a buffer and printed later.
        If you want to output a paragraph separator, either set end=True or tell a single '\n'.
        If you provide format=False, this paragraph of text won't be formatted by textwrap,
        and whitespace is untouched. An empty string isn't outputted at all.
        Multiple messages are separated by a space.
        The player object is returned so you can chain calls.
        """
        super(Player, self).tell(*messages)
        if messages == ("\n",):
            self._output.p()
        else:
            for msg in messages:
                self._output.print(str(msg), **kwargs)
        return self

    def peek_output(self):
        """Returns a copy of the output that sits in the buffer so far."""
        lines = self._output.raw(clear=False)
        return "\n".join(lines)

    def get_raw_output(self):
        """Gets the accumulated output lines in raw form (for test purposes)"""
        return self._output.raw(clear=True)

    def get_output(self):
        """Gets the accumulated output lines, formats them nicely, and clears the buffer"""
        self._output.width = self.screen_width
        output = self._output.render()
        if self.transcript:
            self.transcript.write(output)
        return output

    def look(self, short=None):
        """look around in your surroundings (exclude player from livings)"""
        if short is None:
            if self.brief == 2:
                short = True
            elif self.brief == 1:
                short = self.location in self.known_locations
        if self.location:
            self.known_locations.add(self.location)
            # if "wizard" in self.privileges:
            #    self.tell(repr(self.location), end=True)
            look_paragraphs = self.location.look(exclude_living=self, short=short)
            for paragraph in look_paragraphs:
                self.tell(paragraph, end=True)
        else:
            self.tell("You see nothing.")

    def move(self, target_location, actor=None, silent=False, is_player=True):
        """delegate to Living but with is_player set to True"""
        return super(Player, self).move(target_location, actor, silent, True)

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

    def allow_give_money(self, actor, amount):
        """Do we accept money? Raise ActionRefused if not."""
        pass

    def get_pending_input(self):
        result = []
        self.input_is_available.clear()
        try:
            while True:
                result.append(self._input.get_nowait())
        except queue.Empty:
            return result

    def input_line(self, cmd):
        self._input.put(cmd)
        if self.transcript:
            self.transcript.write("\n\n>> %s\n" % cmd)
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
            self.observer.tell("[wiretap on '%s': %s]" % (self.target_name, msg), end=True)
