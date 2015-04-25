"""
Player code

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import time
from . import base
from . import soul
from . import lang
from . import hints
from . import pubsub
from . import mud_context
from .errors import SecurityViolation, ActionRefused, ParseError
from .util import queue
from .tio.iobase import strip_text_styles
from threading import Event
from .tio import DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_INDENT


class Player(base.Living, pubsub.Listener):
    """
    Player controlled entity.
    Has a Soul for social interaction.
    """
    def __init__(self, name, gender, race="human", description=None, short_description=None):
        title = lang.capital(name)
        super(Player, self).__init__(name, gender, race, title, description, short_description)
        self.soul = soul.Soul()
        self.turns = 0
        self.state = {}
        self.hints = hints.HintSystem()
        self.previous_commandline = None
        self.screen_width = DEFAULT_SCREEN_WIDTH
        self.screen_indent = DEFAULT_SCREEN_INDENT
        self.screen_styles_enabled = True
        self.smartquotes_enabled = True
        self.brief = 0  # 0=off, 1=short descr. for known locations, 2=short descr. for all locations
        self.known_locations = set()
        self.story_complete = False
        self.init_nonserializables()

    def init_nonserializables(self):
        self._input = queue.Queue()
        self.input_is_available = Event()
        self.transcript = None
        self._output = TextBuffer()
        self.io = None  # will be set to appropriate I/O adapter by the driver
        self._previous_parsed = None

    def __repr__(self):
        return "<%s '%s' @ 0x%x, privs:%s>" % (self.__class__.__name__, self.name, id(self), ",".join(self.privileges) or "-")

    def __getstate__(self):
        state = super(Player, self).__getstate__()
        # skip all non-serializable things (or things that need to be reinitialized)
        for name in ["_input", "_output", "input_is_available", "transcript", "io"]:
            del state[name]
        return state

    def __setstate__(self, state):
        super(Player, self).__setstate__(state)
        self.init_nonserializables()

    def set_screen_sizes(self, indent, width):
        self.screen_indent = indent
        self.screen_width = width

    def story_completed(self):
        """
        Call this when the player completed the story.
        It will trigger the game's ending/game-over sequence.
        """
        self.story_complete = True

    def parse(self, commandline, external_verbs=frozenset()):
        """Parse the commandline into something that can be processed by the soul (soul.ParseResult)"""
        if commandline == "again":
            # special case, repeat previous command
            if self.previous_commandline:
                commandline = self.previous_commandline
                self.tell("<dim>(repeat: %s)</>" % commandline, end=True)
            else:
                raise ActionRefused("Can't repeat your previous action.")
        self.previous_commandline = commandline
        parsed = self.soul.parse(self, commandline, external_verbs)
        self._previous_parsed = parsed
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

    def remember_parsed(self):
        """remember the previously parsed data, soul uses this to reference back to earlier items/livings"""
        self.soul.previously_parsed = self._previous_parsed

    def tell(self, *messages, **kwargs):
        """
        A message sent to a player (or multiple messages). They are meant to be printed on the screen.
        For efficiency, messages are gathered in a buffer and printed later.
        If you want to output a paragraph separator, either set end=True or tell a single newline.
        If you provide format=False, this paragraph of text won't be formatted when it is outputted,
        and whitespace is untouched. An empty string isn't outputted at all.
        Multiple messages are separated by a space. The player object is returned so you can chain calls.
        """
        super(Player, self).tell(*messages)
        if messages == ("\n",):
            self._output.p()
        else:
            for msg in messages:
                self._output.print(str(msg), **kwargs)
        return self

    def peek_output_paragraphs_raw(self):
        """
        Returns a copy of the output paragraphs that sit in the buffer so far
        This is for test purposes. No text styles are included.
        """
        paragraphs = self._output.get_paragraphs(clear=False)
        return [strip_text_styles(paragraph_text) for paragraph_text, formatted in paragraphs]

    def get_output_paragraphs_raw(self):
        """
        Gets the accumulated output paragraphs in raw form.
        This is for test purposes. No text styles are included. No IO adapter needs to be initialized.
        """
        paragraphs = self._output.get_paragraphs(clear=True)
        return [strip_text_styles(paragraph_text) for paragraph_text, formatted in paragraphs]

    def get_output(self):
        """
        Gets the accumulated output lines, formats them nicely, and clears the buffer.
        If there is nothing to be outputted, None is returned.
        """
        formatted = self.io.render_output(self._output.get_paragraphs(), width=self.screen_width, indent=self.screen_indent)
        if formatted and self.transcript:
            self.transcript.write(formatted)
        return formatted or None

    def write_output(self):
        """print any buffered output to the player's screen"""
        output = self.get_output()
        if output:
            # (re)set a few io parameters because they can be changed dynamically
            self.io.do_styles = self.screen_styles_enabled
            self.io.do_smartquotes = self.smartquotes_enabled
            if mud_context.config.server_mode == "if" and self.io.output_line_delay > 0:
                for line in output.splitlines():
                    self.io.output(line)
                    self.io.output_delay()
            else:
                self.io.output(output.rstrip())

    def input(self, prompt=None):
        """
        Writes any pending output and prompts for input. Returns stripped result.
        Note that input processing takes place asynchronously so this method just prints
        the input prompt, and sits around waiting for a result to appear in the input buffer.
        """
        self.write_output()
        self.io.output_no_newline(prompt)
        self.input_is_available.wait()
        return self.get_next_input()

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

    def move(self, target, actor=None, silent=False, is_player=True, verb="move"):
        """delegate to Living but with is_player set to True"""
        return super(Player, self).move(target, actor, silent, True, verb)

    def create_wiretap(self, target):
        if "wizard" not in self.privileges:
            raise SecurityViolation("wiretap requires wizard privilege")
        tap = target.get_wiretap()
        tap.subscribe(self)

    def pubsub_event(self, topicname, event):
        sender, message = event
        self.tell("[wiretapped from '%s': %s]" % (sender, message), end=True)

    def clear_wiretaps(self):
        # clear all wiretaps that this player has
        pubsub.unsubscribe_all(self)

    def destroy(self, ctx):
        self.activate_transcript(None, None)
        super(Player, self).destroy(ctx)
        del self.soul   # truly die ;-)
        if self.io:
            self.io.stop_main_loop = True
            self.io.destroy()
            self.io.abort_all_input(self)

    def allow_give_money(self, actor, amount):
        """Do we accept money? Raise ActionRefused if not."""
        pass

    def get_pending_input(self):
        """return the full set of lines in the input buffer (if any)"""
        result = []
        self.input_is_available.clear()
        try:
            while True:
                result.append(self._input.get_nowait())
        except queue.Empty:
            return result

    def get_next_input(self):
        """
        Return just the next single line in the input buffer (if any, otherwise returns None)
        This is useful for instance when you require an immediate answer to a printed question.
        """
        try:
            result = self._input.get_nowait()
            if self._input.qsize() == 0:
                self.input_is_available.clear()
            return result.strip()
        except queue.Empty:
            return None

    def store_input_line(self, cmd):
        """store a line of entered text in the input command buffer"""
        self._input.put(cmd)
        if self.transcript:
            self.transcript.write("\n\n>> %s\n" % cmd)
        self.input_is_available.set()

    def activate_transcript(self, file, vfs):
        if file:
            if self.transcript:
                raise ActionRefused("There's already a transcript being made to " + self.transcript.name)
            self.transcript = vfs.open_write(file, append=True)
            self.tell("Transcript is being written to", self.transcript.name)
            self.transcript.write("\n*Transcript starting at %s*\n\n" % time.ctime())
        else:
            if self.transcript:
                self.transcript.write("\n*Transcript ending at %s*\n\n" % time.ctime())
                self.transcript.close()
                self.transcript = None
                self.tell("Transcript ended.")


class TextBuffer(object):
    class Paragraph(object):
        def __init__(self, format=True):
            self.format = format
            self.lines = []

        def add(self, line):
            self.lines.append(line)

        def text(self):
            return "\n".join(self.lines) + "\n"

    def __init__(self):
        self.init()

    def init(self):
        self.paragraphs = []
        self.in_paragraph = False

    def p(self):
        """Paragraph terminator. Start new paragraph on next line."""
        if not self.in_paragraph:
            self.__new_paragraph(False)
        self.in_paragraph = False

    def __new_paragraph(self, format):
        p = TextBuffer.Paragraph(format)
        self.paragraphs.append(p)
        self.in_paragraph = True
        return p

    def print(self, line, end=False, format=True):
        """
        Write a line of text. A single space is inserted between lines, if format=True.
        If end=True, the current paragraph is ended and a new one begins.
        If format=True, the text will be formatted when output, otherwise it is outputted as-is.
        """
        if not line and format and not end:
            return
        if self.in_paragraph:
            p = self.paragraphs[-1]
        else:
            p = self.__new_paragraph(format)
        if p.format != format:
            p = self.__new_paragraph(format)
        if format:
            line = line.strip()
        p.add(line)
        if end:
            self.in_paragraph = False

    def get_paragraphs(self, clear=True):
        paragraphs = [(p.text(), p.format) for p in self.paragraphs]
        if clear:
            self.init()
        return paragraphs
