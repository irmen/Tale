# coding=utf-8
"""
Player code

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import time
import random
from hashlib import sha1
import shelve
import threading
import datetime
import re
import sys
from contextlib import closing
from . import base
from . import lang
from . import hints
from . import pubsub
from . import mud_context
from . import util
from .errors import ActionRefused
from .util import queue
from .tio.iobase import strip_text_styles
from threading import Event
from .tio import DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_INDENT
try:
    import anydbm as dbm   # python 2
except ImportError:
    try:
        import dbm   # python 3
    except ImportError:
        dbm = None
except Exception as x:
    # pypy can generate a distutils error somehow if dbm is not available
    dbm = None
if sys.version_info < (3, 0):
    input = raw_input
else:
    input = input


class Player(base.Living, pubsub.Listener):
    """
    Player controlled entity.
    Has a Soul for social interaction.
    """
    def __init__(self, name, gender, race="human", description=None, short_description=None):
        title = lang.capital(name)
        super(Player, self).__init__(name, gender, race, title, description, short_description)
        self.turns = 0
        self.state = {}
        self.hints = hints.HintSystem()
        self.screen_width = DEFAULT_SCREEN_WIDTH
        self.screen_indent = DEFAULT_SCREEN_INDENT
        self.screen_styles_enabled = True
        self.smartquotes_enabled = True
        self.output_line_delay = 50   # milliseconds.
        self.brief = 0  # 0=off, 1=short descr. for known locations, 2=short descr. for all locations
        self.known_locations = set()
        self.story_complete = False
        self.last_input_time = time.time()
        self.init_nonserializables()

    def init_nonserializables(self):
        self._input = queue.Queue()
        self.input_is_available = Event()
        self.transcript = None
        self._output = TextBuffer()

    def __repr__(self):
        return "<%s '%s' @ 0x%x, privs:%s>" % (self.__class__.__name__, self.name, id(self), ",".join(self.privileges) or "-")

    def __getstate__(self):
        state = super(Player, self).__getstate__()
        # skip all non-serializable things (or things that need to be reinitialized)
        for name in ["_input", "_output", "input_is_available", "transcript"]:
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

    def tell(self, *messages, **kwargs):
        """
        A message sent to a player (or multiple messages). They are meant to be printed on the screen.
        For efficiency, messages are gathered in a buffer and printed later.
        If you want to output a paragraph separator, either set end=True or tell a single newline.
        If you provide format=False, this paragraph of text won't be formatted when it is outputted,
        and whitespace is untouched. Empty strings aren't outputted at all.
        Multiple messages are separated by a space (or newline, if format=False).
        The player object is returned so you can chain calls.
        """
        super(Player, self).tell(*messages)
        if messages == ("\n",):
            self._output.p()
        else:
            sep = u" " if kwargs.get("format", True) else u"\n"
            if sys.version_info < (3, 0):
                msg = sep.join(unicode(msg) for msg in messages)
            else:
                msg = sep.join(str(msg) for msg in messages)
            self._output.print(msg, **kwargs)
        return self

    def look(self, short=None):
        """look around in your surroundings (it excludes the player himself from livings)"""
        if short is None:
            if self.brief == 2:
                short = True
            elif self.brief == 1:
                short = self.location in self.known_locations
        if self.location:
            self.known_locations.add(self.location)
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
            raise ActionRefused("wiretap requires wizard privilege")
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

    def store_input_line(self, cmd):
        """store a line of entered text in the input command buffer"""
        cmd = cmd.strip()
        self._input.put(cmd)
        if self.transcript:
            self.transcript.write(u"\n\n>> %s\n" % cmd)
        self.input_is_available.set()
        self.last_input_time = time.time()

    @property
    def idle_time(self):
        return time.time() - self.last_input_time

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

    def search_extradesc(self, keyword, include_inventory=True, include_containers_in_inventory=False):
        """
        Searches the extradesc keywords for an location/living/item within the 'visible' world around the player,
        including their inventory.  If there's more than one hit, just return the first extradesc description text.
        """
        assert keyword
        keyword = keyword.lower()
        desc = self.location.extra_desc.get(keyword)
        if desc:
            return desc
        for item in self.location.items:
            desc = item.extra_desc.get(keyword)
            if desc:
                return desc
        for living in self.location.livings:
            desc = living.extra_desc.get(keyword)
            if desc:
                return desc
        if include_inventory:
            for item in self.inventory:
                desc = item.extra_desc.get(keyword)
                if desc:
                    return desc
        if include_containers_in_inventory:
            for container in self.inventory:
                try:
                    inventory = container.inventory
                except ActionRefused:
                    continue    # no access to inventory, just skip this item silently
                else:
                    for item in inventory:
                        desc = item.extra_desc.get(keyword)
                        if desc:
                            return desc
        return None

    def test_peek_output_paragraphs(self):
        """
        Returns a copy of the output paragraphs that sit in the buffer so far
        This is for test purposes. No text styles are included.
        """
        paragraphs = self._output.get_paragraphs(clear=False)
        return [strip_text_styles(paragraph_text) for paragraph_text, formatted in paragraphs]

    def test_get_output_paragraphs(self):
        """
        Gets the accumulated output paragraphs in raw form.
        This is for test purposes. No text styles are included.
        """
        paragraphs = self._output.get_paragraphs(clear=True)
        return [strip_text_styles(paragraph_text) for paragraph_text, formatted in paragraphs]


class TextBuffer(object):
    """
    Buffered output for the text that the player will see on the screen.
    The buffer queues up output text into paragraphs.
    Notice that no actual output formatting is done here, that is performed elsewhere.
    """
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


class PlayerConnection(object):
    """
    Represents a player and the i/o connection that is used for him/her.
    Provides high level i/o operations to input commands and write output for the player.
    Other code should not have to call the i/o adapter directly.
    """
    def __init__(self, player=None, io=None):
        self.player = player
        self.io = io
        self.need_new_input_prompt = True

    def get_output(self):
        """
        Gets the accumulated output lines, formats them nicely, and clears the buffer.
        If there is nothing to be outputted, None is returned.
        """
        formatted = self.io.render_output(self.player._output.get_paragraphs(), width=self.player.screen_width, indent=self.player.screen_indent)
        if formatted and self.player.transcript:
            self.player.transcript.write(formatted)
        return formatted or None

    @property
    def last_output_line(self):
        return self.io.last_output_line

    @property
    def idle_time(self):
        return self.player.idle_time

    def write_output(self):
        """print any buffered output to the player's screen"""
        if not self.io:
            return
        output = self.get_output()
        if output:
            # (re)set a few io parameters because they can be changed dynamically
            self.io.do_styles = self.player.screen_styles_enabled
            self.io.do_smartquotes = self.player.smartquotes_enabled
            if mud_context.config.server_mode == "if" and self.player.output_line_delay > 0:
                for line in output.rstrip().splitlines():
                    self.io.output(line)
                    time.sleep(self.player.output_line_delay / 1000.0)  # delay the output for a short period
            else:
                self.io.output(output.rstrip())

    def output(self, *lines):
        """directly writes the given text to the player's screen, without buffering and formatting/wrapping"""
        self.io.output(*lines)

    def output_no_newline(self, line):
        """similar to output() but writes a single line, without newline at the end"""
        self.io.output_no_newline(line)

    def input_direct(self, prompt=None):
        """
        Writes any pending output and prompts for input directly. Returns stripped result.
        The driver does NOT use this for the regular game loop!
        This call is *blocking* and will not work in a multi user situation.
        """
        assert self.io.supports_blocking_input
        self.write_output()
        if not prompt.endswith(" "):
            prompt += " "
        self.output_no_newline(prompt)
        self.player.input_is_available.wait()   # blocking wait
        self.need_new_input_prompt = True
        return self.player.get_pending_input()[0].strip()   # use just the first line, strip whitespace

    def write_input_prompt(self):
        # only actually write a prompt when the flag is set.
        # this avoids writing a prompt on every server tick even when nothing is entered.
        if self.need_new_input_prompt:
            self.io.write_input_prompt()
            self.need_new_input_prompt = False

    def clear_screen(self):
        self.io.clear_screen()

    def break_pressed(self):
        self.io.break_pressed()

    def critical_error(self):
        self.io.critical_error()

    def singleplayer_mainloop(self):
        return self.io.singleplayer_mainloop(self)

    def pause(self, unpause=False):
        self.io.pause(unpause)

    def destroy(self):
        if self.io:
            self.io.stop_main_loop = True
            self.io.destroy()
            if self.player and mud_context.config.server_mode == "if":
                self.io.abort_all_input(self.player)
            self.io = None
        if self.player:
            ctx = util.Context(mud_context.driver, None, mud_context.config, self)
            self.player.destroy(ctx)
            # self.player = Player("<destroyed-%d>" % id(self.player), "n")
            self.player = None


class MudAccounts(object):
    """Handles the accounts (login, creation, etc) of mud users"""
    def __init__(self, database_opener=None):
        self.open_db = database_opener or self.__shelve_db_opener
        self.db_lock = threading.Lock()
        try:
            self.get("trigger")
        except KeyError:
            pass

    def __shelve_db_opener(self):
        """If not specified, a simple shelve database is used in the user's data directry"""
        # XXX shelve doesn't work correctly with IronPython (crashes with a TypeError)... replace this with sqlite3?
        dbpath = mud_context.driver.user_resources.validate_path("useraccounts.shelve")
        try:
            return closing(shelve.open(dbpath, flag='w'))
        except dbm.error:
            print("%s: Can't open the user accounts database." % mud_context.config.name)
            print("Location:", dbpath)
            response = input("\nDo you want to create a new one? ")
            if lang.yesno(response):
                return closing(shelve.open(dbpath, flag='c'))
            else:
                raise SystemExit("Cannot launch mud mode without a user accounts database.")

    def __shelve_encode_key(self, key):
        if sys.version_info < (3, 0):
            return key.encode("utf-8")
        return key

    def get(self, name):
        name = self.__shelve_encode_key(name)
        with self.db_lock, self.open_db() as db:
            return db[name]

    def all_accounts(self):
        with self.db_lock, self.open_db() as db:
            return dict(db)

    def logged_in(self, name):
        name = self.__shelve_encode_key(name)
        with self.db_lock, self.open_db() as db:
            account = db[name]
            account["logged_in"] = str(datetime.datetime.now().replace(microsecond=0))
            db[name] = account

    def valid_password(self, name, password):
        name = self.__shelve_encode_key(name)
        with self.db_lock, self.open_db() as db:
            if name in db:
                account = db[name]
                pwhash, _ = self._pwhash(password, account["pw_salt"])
                if pwhash == account["pw_hash"]:
                    return
            raise ValueError("Invalid name or password.")

    @staticmethod
    def _pwhash(password, salt=None):
        if not salt:
            salt = str(random.random() * time.time() + id(password)).replace('.', '')
        pwhash = sha1((salt + password).encode("utf-8")).hexdigest()
        return pwhash, salt

    @staticmethod
    def accept_password(password):
        if len(password) >= 6:
            if re.search("[a-zA-z]", password) and re.search("[0-9]", password):
                return password
        raise ValueError("Password should be minimum length 6. It should contain letters, at least one number, and optionally other characters.")

    @staticmethod
    def accept_name(name):
        if re.match("[a-z]{3,16}$", name):
            if name in MudAccounts.blocked_names:
                raise ValueError("That name is not available.")
            return name
        raise ValueError("Name should be all lowercase letters [a-z] and length 3 to 16.")

    @staticmethod
    def accept_email(email):
        user, _, domain = email.partition("@")
        if user and domain and user.strip() == user and domain.strip() == domain:
            return email
        raise ValueError("Invalid email address.")

    def create(self, name, password, email, gender, stats, privileges=[]):
        name = name.strip()
        dbname = self.__shelve_encode_key(name)
        email = email.strip()
        gender = gender.strip()
        self.accept_name(name)
        with self.db_lock, self.open_db() as db:
            if dbname in db:
                raise ValueError("That name is not available.")
            self.accept_password(password)
            self.accept_email(email)
            pwhash, salt = self._pwhash(password)
            db[dbname] = {"name": name,
                          "email": email,
                          "pw_hash": pwhash,
                          "pw_salt": salt,
                          "privileges": privileges,
                          "gender": gender,
                          "stats": stats,
                          "created": str(datetime.datetime.now().replace(microsecond=0)),
                          "logged_in": None}
            return db[dbname]

    def change_password_email(self, name, old_password, new_password=None, new_email=None):
        self.valid_password(name, old_password)
        name = self.__shelve_encode_key(name)
        with self.db_lock, self.open_db() as db:
            if name not in db:
                raise KeyError("Unknown name.")
            account = db[name]
            if new_password:
                self.accept_password(new_password)
                pwhash, salt = self._pwhash(new_password)
                account["pw_hash"] = pwhash
                account["pw_salt"] = salt
            new_email = new_email.strip() if new_email else None
            if new_email:
                self.accept_email(new_email)
                account["email"] = new_email
            db[name] = account

    @util.authorized("wizard")
    def update_privileges(self, name, privileges, actor):
        name = self.__shelve_encode_key(name)
        with self.db_lock, self.open_db() as db:
            if name not in db:
                raise KeyError("Unknown name.")
            account = db[name]
            account["privileges"] = set(privileges)
            db[name] = account

    blocked_names = """irmen
me
you
us
them
they
their
theirs
he
him
his
she
her
hers
it
its
yes
no
god
allah
jesus
jezus
hitler
neuk
fuck
cunt
cock
prick
pik
lul
kut
dick
pussy
twat
cum
milf
anal
sex
ass
asshole
neger
nigger
nigga
jew
muslim
moslim
binladen
chink
cancer
kanker
aids
bitch
motherfucker
fucker
""".split()
