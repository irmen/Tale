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
import textwrap
from . import base, soul
from . import lang, util
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
        self.score = 0
        self.turns = 0
        self.previous_commandline = None
        self.screen_width = 75
        self.screen_indent = 2
        self.brief = 0  # 0=off, 1=short descr. for known locations, 2=short descr. for all locations
        self.known_locations = set()
        self.init_nonserializables()

    def init_nonserializables(self):
        self.installed_wiretaps = set()
        self._input = queue.Queue()
        self.input_is_available = Event()
        self.transcript = None
        self._output = []
        indent = " " * self.screen_indent
        self.textwrapper = textwrap.TextWrapper(initial_indent=indent, subsequent_indent=indent,
                                                width=self.screen_width, fix_sentence_endings=True)

    def __repr__(self):
        return "<%s.%s '%s' @ 0x%x, privs:%s>" % (self.__class__.__module__, self.__class__.__name__,
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

    def parse(self, commandline, external_verbs=frozenset(), room_exits=None):
        """Parse the commandline into something that can be processed by the soul (soul.ParseResult)"""
        if commandline == "again":
            # special case, repeat previous command
            if self.previous_commandline:
                commandline = self.previous_commandline
                self.tell("(repeat: %s)" % commandline)
            else:
                raise ActionRefused("Can't repeat your previous action.")
        self.previous_commandline = commandline
        parsed = self.soul.parse(self, commandline, external_verbs, room_exits)
        if external_verbs and parsed.verb in external_verbs:
            raise soul.NonSoulVerb(parsed)
        if parsed.verb not in soul.NONLIVING_OK_VERBS:
            # check if any of the targeted objects is a non-living
            if not all(isinstance(who, base.Living) for who in parsed.who_order):
                raise soul.NonSoulVerb(parsed)
        return parsed

    def socialize_parsed(self, parsed):
        """Don't re-parse the command string, but directly feed the parse results we've already got into the Soul"""
        return self.soul.process_verb_parsed(self, parsed)

    def tell(self, *messages, **kwargs):
        """
        A message sent to a player (or multiple messages). They are meant to be printed on the screen.
        For efficiency, messages are gathered in a buffer and printed later.
        If you want to output a paragraph separator, either set end=True or tell a single '\n'.
        If you provide format=False, this paragraph of text won't be formatted by textwrap,
        and whitespace is untouched.
        """
        super(Player, self).tell(*messages)
        if messages == ("\n",):
            self._output.append("\n")  # single newline = paragraph separator
        else:
            kws = set(kwargs) - {"format", "end"}
            assert not kws, "only 'format' and 'end' keywords are understood"
            do_format = kwargs.get("format", True)
            do_paragraph = kwargs.get("end", False)
            if do_format:
                txt = " ".join(str(msg).strip() for msg in messages)
            else:
                txt = "".join(str(msg) for msg in messages)
                txt = "\a" + txt  # \a is a special control char meaning 'don't format this'
                do_paragraph = True
            self._output.append(txt)
            if do_paragraph:
                self._output.append("\n")  # paragraph separator

    def get_output_lines(self):
        """
        Gets the accumulated output lines and clears the buffer.
        Deprecated: use get_wrapped_output_lines instead.
        """
        lines = self._output
        self._output = []
        if self.transcript:
            self.transcript.writelines(lines)
        return lines

    def get_wrapped_output_lines(self):
        """gets the accumulated output lines, formats them nicely, and clears the buffer"""
        lines = self._output
        self._output = []
        output = []
        for paragraph in util.split_paragraphs(lines):
            if paragraph.startswith("\a"):
                # \a means: don't format this
                paragraph = paragraph[1:]
                if self.screen_indent:
                    indent = " " * self.screen_indent
                    paragraph = paragraph.splitlines()
                    for i in range(len(paragraph)):
                        paragraph[i] = indent + paragraph[i]
                    paragraph = "\n".join(paragraph)
            else:
                self.textwrapper.width = self.screen_width
                paragraph = self.textwrapper.fill(paragraph)
            output.append(paragraph)
        output = "\n".join(output)  # paragraphs are separated on screen by a newline
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
            if "wizard" in self.privileges:
                self.tell(repr(self.location), end=True)
            look_paragraphs = self.location.look(exclude_living=self, short=short)
            for paragraph in look_paragraphs:
                self.tell(paragraph, end=True)
        else:
            self.tell("You see nothing.")

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
