# coding=utf-8
"""
Player code

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import time
import random
import sqlite3
import queue
import datetime
import re
from hashlib import sha1
from . import base
from . import lang
from . import hints
from . import pubsub
from . import mud_context
from . import util
from .errors import ActionRefused
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
    """
    Handles the accounts (login, creation, etc) of mud users

    Database:
        account(name, email, pw_hash, pw_salt, created, logged_in, locked)
        privilege(account, privilege)
        charstat(account, gender, stat1, stat2,...) @todo
    """

    class Account:
        def __init__(self, name, email, pw_hash, pw_salt, privileges, created, logged_in, stats):
            # validation on the suitability of names, emails etc is taken care of by the creating code
            self.name = name
            self.email = email
            self.pw_hash = pw_hash
            self.pw_salt = pw_salt
            self.privileges = privileges or set()  # simply a set of strings
            self.created = created
            self.logged_in = logged_in
            self.stats = stats   # @todo

    def __init__(self, databasefile=None):
        self.sqlite_dbpath = databasefile or mud_context.driver.user_resources.validate_path("useraccounts.sqlite")
        self._create_database()

    def _sqlite_connect(self):
        conn = sqlite3.connect(self.sqlite_dbpath, detect_types=sqlite3.PARSE_DECLTYPES, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _create_database(self):
        try:
            with self._sqlite_connect() as conn:
                table_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Account'").fetchone()
                if not table_exists:
                    print("%s: Creating new user accounts database." % mud_context.config.name)
                    print("Location:", self.sqlite_dbpath, "\n")
                    # create the schema
                    conn.execute("""
                        CREATE TABLE Account(
                            id integer PRIMARY KEY,
                            name varchar NOT NULL,
                            email varchar NOT NULL,
                            pw_hash varchar NOT NULL,
                            pw_salt varchar NOT NULL,
                            created timestamp NOT NULL,
                            logged_in timestamp NULL
                        );""")
                    conn.execute("CREATE INDEX idx_account_name ON Account(name)")
                    conn.execute("""
                        CREATE TABLE Privilege(
                            id integer PRIMARY KEY,
                            account integer NOT NULL,
                            privilege varchar NOT NULL,
                            FOREIGN KEY(account) REFERENCES Account(id)
                        );""")
                    conn.execute("CREATE INDEX idx_privilege_account ON Privilege(account)")
                    conn.execute("""
                        CREATE TABLE CharStat(
                            id integer PRIMARY KEY,
                            account integer NOT NULL,
                            gender char(1) NOT NULL,
                            FOREIGN KEY(account) REFERENCES Account(id)
                        );
                        """)
                    conn.commit()
        except sqlite3.Error as x:
            print("%s: Can't open or create the user accounts database." % mud_context.config.name)
            print("Location:", self.sqlite_dbpath)
            print("Error:", repr(x))
            raise SystemExit("Cannot launch mud mode without a user accounts database.")

    def get(self, name):
        with self._sqlite_connect() as conn:
            result = conn.execute("SELECT id FROM Account WHERE name=?", (name,)).fetchone()
            if not result:
                raise KeyError(name)
            return self._fetch_account(conn, result["id"])

    def _fetch_account(self, conn, account_id):
        result = conn.execute("SELECT * FROM Account WHERE id=?", (account_id,)).fetchone()
        priv_result = conn.execute("SELECT privilege FROM Privilege WHERE account=?", (account_id,)).fetchall()
        privileges = {pr["privilege"] for pr in priv_result}
        stats = None   # @ todo
        return MudAccounts.Account(result["name"], result["email"], result["pw_hash"], result["pw_salt"],
                                   privileges, result["created"], result["logged_in"], stats)

    def all_accounts(self, having_privilege=None):
        with self._sqlite_connect() as conn:
            if having_privilege:
                result = conn.execute("SELECT a.id FROM Account a INNER JOIN Privilege p ON p.account=a.id AND p.privilege=?", (having_privilege,)).fetchall()
            else:
                result = conn.execute("SELECT id FROM Account").fetchall()
            account_ids = [ar["id"] for ar in result]
            accounts = {self._fetch_account(conn, account_id) for account_id in account_ids}
            return accounts

    def logged_in(self, name):
        timestamp = datetime.datetime.now().replace(microsecond=0)
        with self._sqlite_connect() as conn:
            conn.execute("UPDATE Account SET logged_in=? WHERE name=?", (timestamp, name))

    def valid_password(self, name, password):
        with self._sqlite_connect() as conn:
            result = conn.execute("SELECT pw_hash, pw_salt FROM Account WHERE name=?", (name,)).fetchone()
        if result:
            stored_hash, stored_salt = result["pw_hash"], result["pw_salt"]
            pwhash, _ = self._pwhash(password, stored_salt)
            if pwhash == stored_hash:
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

    @staticmethod
    def accept_privilege(priv):
        if priv not in {"wizard"}:
            raise ValueError("Invalid privilege: "+priv)

    def create(self, name, password, email, gender, stats, privileges=[]):
        name = name.strip()
        email = email.strip()
        gender = gender.strip()   # @todo move gender to stats instead of on account directly
        self.accept_name(name)
        self.accept_password(password)
        self.accept_email(email)
        privileges = {p.strip() for p in privileges}
        for p in privileges:
            self.accept_privilege(p)
        created = datetime.datetime.now().replace(microsecond=0)
        pwhash, salt = self._pwhash(password)
        with self._sqlite_connect() as conn:
            result = conn.execute("SELECT COUNT(*) FROM Account WHERE name=?", (name,)).fetchone()[0]
            if result > 0:
                raise ValueError("That name is not available.")
            result = conn.execute("INSERT INTO Account('name', 'email', 'pw_hash', 'pw_salt', 'created') VALUES (?,?,?,?,?)", (name, email, pwhash, salt, created))
            for privilege in privileges:
                conn.execute("INSERT INTO Privilege(account, privilege) VALUES (?,?)", (result.lastrowid, privilege))
            # @todo store the stats
        return MudAccounts.Account(name, email, pwhash, salt, privileges, created, None, stats)

    def change_password_email(self, name, old_password, new_password=None, new_email=None):
        self.valid_password(name, old_password)
        new_email = new_email.strip() if new_email else None
        if new_password:
            self.accept_password(new_password)
        if new_email:
            self.accept_email(new_email)
        with self._sqlite_connect() as conn:
            result = conn.execute("SELECT id FROM Account WHERE name=?", (name,)).fetchone()
            if not result:
                raise KeyError("Unknown name.")
            account_id = result["id"]
            if new_password:
                pwhash, salt = self._pwhash(new_password)
                conn.execute("UPDATE Account SET pw_hash=?, pw_salt=? WHERE id=?", (pwhash, salt, account_id))
            if new_email:
                conn.execute("UPDATE Account SET email=? WHERE id=?", (new_email, account_id))

    @util.authorized("wizard")
    def update_privileges(self, name, privileges, actor):
        privileges = {p.strip() for p in privileges}
        for p in privileges:
            self.accept_privilege(p)
        with self._sqlite_connect() as conn:
            result = conn.execute("SELECT id FROM Account WHERE name=?", (name,)).fetchone()
            if not result:
                raise KeyError("Unknown name.")
            account_id = result["id"]
            conn.execute("DELETE FROM Privilege WHERE account=?", (account_id,))
            for privilege in privileges:
                conn.execute("INSERT INTO Privilege(account, privilege) VALUES (?,?)", (account_id, privilege))
        return privileges

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
