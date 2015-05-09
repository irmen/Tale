# coding=utf-8
"""
Mud driver (server).

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import collections
from functools import total_ordering
import datetime
import sys
import time
import os
import heapq
import argparse
import pickle
import threading
import types
import traceback
import appdirs
import distutils.version
from . import mud_context
from . import errors
from . import util
from . import soul
from . import cmds
from . import player
from . import __version__ as tale_version_str
from .tio import vfs
from .tio import DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_DELAY


@total_ordering
class Deferred(object):
    """
    Represents a callable action that will be invoked (with the given arguments) sometime in the future.
    This object captures the action that must be invoked in a way that is serializable.
    That means that you can't pass all types of callables, there are a few that are not
    serializable (lambda's and scoped functions). They will trigger an error if you use those.
    """
    def __init__(self, due, action, vargs, kwargs):
        assert due is None or isinstance(due, datetime.datetime)
        assert callable(action)
        self.due = due   # in game time
        self.owner = getattr(action, "__self__", None)
        if isinstance(self.owner, types.ModuleType):
            # encode a module simply by its name
            self.owner = "module:" + self.owner.__name__
        if self.owner is None:
            action_module = getattr(action, "__module__", None)
            if action_module:
                if hasattr(sys.modules[action_module], action.__name__):
                    self.owner = "module:" + action_module
                else:
                    # a callable was passed that we cannot serialize.
                    raise ValueError("cannot use scoped functions or lambdas as deferred: " + str(action))
            else:
                raise ValueError("cannot determine action's owner object: " + str(action))
        self.action = action.__name__    # store name instead of object, to make this serializable
        self.vargs = vargs
        self.kwargs = kwargs

    def __eq__(self, other):
        return self.due == other.due and type(self.owner) == type(other.owner)\
            and self.action == other.action and self.vargs == other.vargs and self.kwargs == other.kwargs

    def __lt__(self, other):
        return self.due < other.due   # deferreds must be sortable

    def when_due(self, game_clock, realtime=False):
        """
        In what time is this deferred due to occur? (timedelta)
        Normally it is in terms of game-time, but if you pass realtime=True,
        you will get the real-time timedelta.
        """
        secs = (self.due - game_clock.clock).total_seconds()
        if realtime:
            secs = int(secs / game_clock.times_realtime)
        return datetime.timedelta(seconds=secs)

    def __call__(self, *args, **kwargs):
        self.kwargs = self.kwargs or {}
        if "ctx" in kwargs:
            self.kwargs["ctx"] = kwargs["ctx"]  # add a 'ctx' keyword argument to the call for convenience
        if isinstance(self.action, util.basestring_type):
            # deferred action is stored as the name of the function to call,
            # so we need to obtain the actual function from the owner object.
            if isinstance(self.owner, util.basestring_type):
                if self.owner.startswith("module:"):
                    # the owner refers to a module
                    self.owner = sys.modules[self.owner[7:]]
                else:
                    raise RuntimeError("invalid owner specifier: " + self.owner)
            func = getattr(self.owner, self.action)
            func(*self.vargs, **self.kwargs)
        else:
            self.action(*self.vargs, **self.kwargs)
        # our lifetime has ended, remove references:
        del self.owner
        del self.action
        del self.kwargs
        del self.vargs


class Commands(object):
    def __init__(self):
        self.commands_per_priv = {None: {}}
        self.no_soul_parsing = set()

    def add(self, verb, func, privilege=None):
        self.validateFunc(func)
        for commands in self.commands_per_priv.values():
            if verb in commands:
                raise ValueError("command defined more than once: " + verb)
        self.commands_per_priv.setdefault(privilege, {})[verb] = func

    def override(self, verb, func, privilege=None):
        self.validateFunc(func)
        if verb in self.commands_per_priv[privilege]:
            existing = self.commands_per_priv[privilege][verb]
            self.commands_per_priv[privilege][verb] = func
            return existing
        raise KeyError("command not defined: " + verb)

    def validateFunc(self, func):
        if not hasattr(func, "is_tale_command_func"):
            raise ValueError("the function '%s' is not a proper command function (did you forget the decorator?)" % func.__name__)

    def get(self, privileges):
        result = self.commands_per_priv[None]  # always include the cmds for None
        for priv in privileges:
            if priv in self.commands_per_priv:
                result.update(self.commands_per_priv[priv])
        return result

    def adjust_available_commands(self, story_config):
        # disable commands flagged with the given game_mode
        # disable soul verbs flagged with override
        # mark non-soul commands
        for commands in self.commands_per_priv.values():
            for cmd, func in list(commands.items()):
                disabled_mode = getattr(func, "disabled_in_mode", None)
                if story_config.server_mode == disabled_mode:
                    del commands[cmd]
                elif getattr(func, "overrides_soul", False):
                    del soul.VERBS[cmd]
                if getattr(func, "no_soul_parse", False):
                    self.no_soul_parsing.add(cmd)


class Driver(object):
    """
    The Mud 'driver'.
    Reads story file and config, initializes game state.
    Handles main game loop, player connections, and loading/saving of game state.
    """
    directions = {"north", "east", "south", "west", "northeast", "northwest", "southeast", "southwest", "up", "down"}

    def __init__(self):
        self.heartbeat_objects = set()
        self.unbound_exits = []
        self.deferreds = []  # heapq
        self.deferreds_lock = threading.Lock()
        self.action_queue = util.queue.Queue()
        self.server_started = datetime.datetime.now().replace(microsecond=0)
        self.config = None
        self.server_loop_durations = collections.deque(maxlen=10)
        self.commands = Commands()
        cmds.register_all(self.commands)
        self.all_players = {}   # maps playername to player connection object
        self.zones = None
        self.moneyfmt = None
        self.resources = self.user_resources = None
        self.story = None
        self.game_clock = None
        self.__stop_mainloop = True
        self.mud_wsgi_server = None

    def start(self, command_line_args):
        """Parse the command line arguments and start the driver accordingly."""
        parser = argparse.ArgumentParser(description="""
            Tale framework %s game driver. Use this to launch a game and specify some settings.
            Sometimes the game will provide its own startup script that invokes this automatically.
            If it doesn't, refer to the options to see how to launch it manually instead.
            """ % tale_version_str)
        parser.add_argument('-g', '--game', type=str, help='path to the game directory', required=True)
        parser.add_argument('-d', '--delay', type=int, help='screen output delay for IF mode (milliseconds, 0=no delay)', default=DEFAULT_SCREEN_DELAY)
        parser.add_argument('-m', '--mode', type=str, help='game mode, default=if', default="if", choices=["if", "mud"])
        parser.add_argument('-i', '--gui', help='gui interface', action='store_true')
        parser.add_argument('-w', '--web', help='web browser interface', action='store_true')
        parser.add_argument('-v', '--verify', help='only verify the story files, dont run it', action='store_true')
        args = parser.parse_args(command_line_args)
        try:
            self.__start(args)
        except Exception:
            if args.gui:
                tb = traceback.format_exc()
                from .tio import tkinter_io
                tkinter_io.show_error_dialog("Exception during start", "An error occurred while starting up the game:\n\n" + tb)
            raise

    def __start(self, args):
        """Start the driver from a parsed set of arguments"""
        if os.path.isdir(args.game):
            # cd into the game directory (we can import it then), and load its config and zones
            os.chdir(args.game)
            sys.path.insert(0, os.curdir)
        elif os.path.isfile(args.game):
            # the game argument points to a file, assume it is a zipfile, add it to the import path
            sys.path.insert(0, args.game)
        else:
            raise IOError("Cannot find specified game")
        story = __import__("story", level=0)
        self.story = story.Story()
        if args.mode not in self.story.config.supported_modes:
            raise ValueError("driver mode '%s' not supported by this story" % args.mode)
        self.config = StoryConfig.copy_from(self.story.config)
        self.config.server_mode = args.mode  # if/mud driver mode ('if' = single player interactive fiction, 'mud'=multiplayer)
        if self.config.server_mode != "if" and self.config.server_tick_method == "command":
            raise ValueError("'command' tick method can only be used in 'if' game mode")
        # Register the driver and some other stuff in the global context.
        mud_context.driver = self
        mud_context.config = self.config
        try:
            story_cmds = __import__("cmds", level=0)
        except (ImportError, ValueError):
            pass
        else:
            story_cmds.register_all(self.commands)
        self.commands.adjust_available_commands(self.config)
        tale_version = distutils.version.LooseVersion(tale_version_str)
        tale_version_required = distutils.version.LooseVersion(self.config.requires_tale)
        if tale_version < tale_version_required:
            raise RuntimeError("The game requires tale " + self.config.requires_tale + " but " + tale_version_str + " is installed.")
        self.game_clock = util.GameDateTime(self.config.epoch or self.server_started, self.config.gametime_to_realtime)
        self.moneyfmt = util.MoneyFormatter(self.config.money_type) if self.config.money_type else None
        self.resources = vfs.VirtualFileSystem(root_package="story")   # read-only story resources
        user_data_dir = appdirs.user_data_dir("Tale", "Razorvine", roaming=True)
        if not os.path.isdir(user_data_dir):
            try:
                os.makedirs(user_data_dir, mode=0o700)
            except os.error:
                pass
        self.user_resources = vfs.VirtualFileSystem(root_path=user_data_dir, readonly=False)  # r/w to the local 'user data' directory
        self.story.init(self)
        import zones
        self.zones = zones
        self.config.startlocation_player = self.__lookup_location(self.config.startlocation_player)
        self.config.startlocation_wizard = self.__lookup_location(self.config.startlocation_wizard)
        if self.config.server_tick_method == "command":
            # If the server tick is synchronized with player commands, this factor needs to be 1,
            # because at every command entered the game time simply advances 1 x server_tick_time.
            self.config.gametime_to_realtime = 1
        assert self.config.server_tick_time > 0
        assert self.config.max_wait_hours >= 0
        self.game_clock = util.GameDateTime(self.config.epoch or self.server_started, self.config.gametime_to_realtime)
        # convert textual exit strings to actual exit object bindings
        for x in self.unbound_exits:
            x._bind_target(self.zones)
        del self.unbound_exits
        if args.verify:
            print("Story: '%s' v%s, by %s." % (self.story.config.name, self.story.config.version, self.story.config.author))
            print("Verified, all seems to be fine.")
            return
        if args.delay < 0 or args.delay > 100:
            raise ValueError("invalid delay, valid range is 0-100")
        if self.config.server_mode == "if":
            # create the single player mode player automatically
            if args.gui:
                player_io = "gui"
            elif args.web:
                player_io = "web"
            else:
                player_io = "console"
            connection = self.__connect_if_player(player_io, args.delay)
            mud_context.player = connection.player
            mud_context.conn = connection
            # the driver mainloop runs in a background thread, the io-loop/gui-event-loop runs in the main thread
            driver_thread = threading.Thread(name="driver", target=self.__startup_main_loop)
            driver_thread.daemon = True
            driver_thread.start()
            connection.singleplayer_mainloop()
        else:
            # mud mode, driver runs as main thread
            mud_context.player = mud_context.conn = None
            self.__print_game_intro(None)
            self.__startup_main_loop()

    def __startup_main_loop(self):
        # continues the startup process and kick off the driver's main loop
        self.__stop_mainloop = False
        try:
            if self.config.server_mode == "if":
                # single player interactive fiction
                while not mud_context.conn:
                    time.sleep(0.02)
                self.__create_player(mud_context.conn)
                mud_context.player.look(short=False)   # force a 'look' command to get our bearings
                mud_context.conn.write_output()
                while not self.__stop_mainloop:
                    self.__main_loop_singleplayer(mud_context.conn)
            else:
                # spin up a multiuser web server
                from .tio.mud_browser_io import TaleMudWsgiApp
                self.mud_wsgi_server = TaleMudWsgiApp.create_app_server(self)
                url = "http://%s:%d/tale/" % self.mud_wsgi_server.server_address
                print("\nPoint your browser to the following url: ", url, end="\n\n")
                while not self.__stop_mainloop:
                    self.__main_loop_multiplayer()
        except:
            for conn in self.all_players.values():
                conn.critical_error()
            self.__stop_mainloop = True
            raise

    def __connect_if_player(self, player_io, line_delay):
        connection = player.PlayerConnection()
        connect_name = "<connecting_%d>" % id(connection)  # unique temporary name
        new_player = player.Player(connect_name, "n", "elemental", "This player is still connecting to the game.")
        if player_io == "gui":
            from .tio.tkinter_io import TkinterIo
            io = TkinterIo(self.config, connection)
        elif player_io == "web":
            from .tio.if_browser_io import HttpIo, TaleWsgiApp
            wsgi_server = TaleWsgiApp.create_app_server(self, connection)
            io = HttpIo(connection, wsgi_server)
        elif player_io == "console":
            from .tio.console_io import ConsoleIo
            io = ConsoleIo(connection)
            io.install_tab_completion(self)
        else:
            raise ValueError("invalid io type")
        connection.player = new_player
        connection.io = io
        self.all_players[new_player.name] = connection
        new_player.output_line_delay = line_delay
        connection.clear_screen()
        self.__print_game_intro(connection)
        return connection

    def _connect_mud_player(self):
        connection = player.PlayerConnection()
        connect_name = "<connecting_%d>" % id(connection)  # unique temporary name
        new_player = player.Player(connect_name, "n", "elemental", "This player is still connecting to the game.")
        connection.player = new_player
        from .tio.mud_browser_io import MudHttpIo
        connection.io = MudHttpIo(connection, self.mud_wsgi_server)
        self.all_players[new_player.name] = connection
        connection.clear_screen()
        self.__print_game_intro(connection)
        new_player.tell("Creating a mud player or logging in is not yet possible!", end=True)  # @todo __create_player
        # @todo the following commands only after properly logging in:
        self.show_motd(new_player, True)
        new_player.look(short=False)  # force a 'look' command to get our bearings
        return connection

    def _disconnect_mud_player(self, conn):
        name = conn.player.name
        assert self.all_players[name] is conn
        conn.write_output()
        conn.destroy()
        del self.all_players[name]

    def __print_game_intro(self, player_connection):
        try:
            # print game banner as supplied by the game
            banner = self.resources["messages/banner.txt"].data
            if player_connection:
                player_connection.player.tell("<bright>" + banner + "</>", format=False)
                player_connection.player.tell("\n")
            else:
                print(banner)
        except IOError:
            # no banner provided by the game, print default game header
            if player_connection:
                o = player_connection.output
                o("")
                o("")
                o("<monospaced><bright>")
                o(("'%s'" % self.config.name).center(DEFAULT_SCREEN_WIDTH))
                o(("v" + self.config.version).center(DEFAULT_SCREEN_WIDTH))
                o("")
                o(("written by " + self.config.author).center(DEFAULT_SCREEN_WIDTH))
                if self.config.author_address:
                    o(self.config.author_address.center(DEFAULT_SCREEN_WIDTH))
                o("</></monospaced>")
                o("")
                o("")
        if not player_connection:
            print("\n")
            print("Tale library:", tale_version_str)
            print("MudLib:       %s, v%s" % (self.config.name, self.config.version))
            if self.config.author:
                print("Written by:   %s - %s" % (self.config.author, self.config.author_address or ""))
            print("Driver start:", time.ctime())
            print("\n")

    def __create_player(self, conn):
        # Lets the user create a new player, load a saved game, or initialize it directly from the story's configuration
        player = conn.player
        if self.config.server_mode == "mud" or not self.config.savegames_enabled:
            load_saved_game = False
        else:
            player.tell("\n")
            load_saved_game = conn.input_confirm("\nDo you want to load a saved game ('<bright>n</>' will start a new game)?")
        player.tell("\n")
        if load_saved_game:
            loaded_player = self.__load_saved_game()
            if loaded_player:
                conn.player = player = loaded_player
                player.tell("\n")
                if self.config.server_mode == "if":
                    self.story.welcome_savegame(player)
                else:
                    player.tell("Welcome back to %s, %s." % (self.config.name, player.title))
                player.tell("\n")
            else:
                load_saved_game = False
        if not load_saved_game:
            if self.config.server_mode == "if" and self.config.player_name:
                # interactive fiction mode, create the player from the game's config
                player.init_names(self.config.player_name, None, None, None)
                player.init_race(self.config.player_race, self.config.player_gender)
            elif self.config.server_mode == "mud" or not self.config.player_name:
                # mud mode, or if mode without player config: create a character with the builder
                from .charbuilder import CharacterBuilder
                name_info = CharacterBuilder(conn).build()
                del self.all_players[player.name]
                self.all_players[name_info.name] = conn
                name_info.apply_to(player)
            player.tell("\n")
            # move the player to the starting location
            if "wizard" in player.privileges:
                player.move(self.config.startlocation_wizard)
            else:
                player.move(self.config.startlocation_player)
            player.tell("\n")
            if self.config.server_mode == "if":
                self.story.welcome(player)
            else:
                player.tell("Welcome to %s, %s." % (self.config.name, player.title), end=True)
            player.tell("\n")
        self.story.init_player(player)

    def _stop_driver(self):
        """
        Stop the driver mainloop in an orderly fashion.
        Flushes any pending output to the players, then closes down.
        """
        self.__stop_mainloop = True
        for conn in self.all_players.values():
            conn.write_output()
            conn.destroy()
        self.all_players.clear()
        time.sleep(0.1)
        mud_context.player = None
        mud_context.conn = None

    def __main_loop_singleplayer(self, conn):
        """
        The game loop, for the single player Interactive Fiction game mode.
        Until the game is exited, it processes player input, and prints the resulting output.
        """
        conn.write_output()
        loop_duration = 0
        previous_server_tick = 0
        while not self.__stop_mainloop:
            conn.write_input_prompt()
            if self.config.server_tick_method == "command":
                # wait indefinitely for next player input
                conn.player.input_is_available.wait()   # blocking wait until playered entered something
                has_input = True
            elif self.config.server_tick_method == "timer":
                # server tick goes on a timer, wait a limited time for player input before going on
                input_wait_time = max(0.01, self.config.server_tick_time - loop_duration)
                has_input = conn.player.input_is_available.wait(input_wait_time)

            loop_start = time.time()
            if has_input:
                conn.need_new_input_prompt = True
                try:
                    self.__server_loop_process_player_input(conn)
                except (KeyboardInterrupt, EOFError):
                    continue
                except errors.StoryCompleted:
                    conn.player.story_completed()
                except errors.SessionExit:
                    self.story.goodbye(conn.player)
                    self._stop_driver()
                    break
                except Exception:
                    txt = "* internal error:\n" + traceback.format_exc()
                    conn.player.tell(txt, format=False)
            # server TICK and pending Actions
            now = time.time()
            if now - previous_server_tick >= self.config.server_tick_time:
                self.__server_tick()
                previous_server_tick = now
            self.__server_loop_process_action_queue()
            # check if player reached the end of the story
            loop_duration = time.time() - loop_start
            self.server_loop_durations.append(loop_duration)
            if conn.player.story_complete:
                self.__story_complete_output(conn)
                self._stop_driver()
            else:
                conn.write_output()

    def __server_loop_process_player_input(self, conn):
        p = conn.player
        assert p.input_is_available.is_set()
        for cmd in p.get_pending_input():
            if not cmd:
                continue
            try:
                p.tell("\n")
                self.__process_player_command(cmd, conn)
                p.remember_parsed()
                # to avoid flooding/abuse, we stop the loop after processing one command.
                break
            except soul.UnknownVerbException as x:
                if x.verb in self.directions:
                    p.tell("You can't go in that direction.")
                else:
                    p.tell("The verb '%s' is unrecognized." % x.verb)
            except errors.ActionRefused as x:
                p.remember_parsed()
                p.tell(str(x))
            except errors.ParseError as x:
                p.tell(str(x))

    def __server_loop_process_action_queue(self):
        while True:
            try:
                action = self.action_queue.get_nowait()
            except util.queue.Empty:
                break
            else:
                try:
                    action()
                except Exception:
                    self.__report_deferred_exception(action)

    def __main_loop_multiplayer(self):
        """
        The game loop, for the multiplayer MUD mode.
        Until the server is shut down, it processes player input, and prints the resulting output.
        """
        loop_duration = 0
        previous_server_tick = 0
        while not self.__stop_mainloop:
            for conn in self.all_players.values():
                conn.write_output()
                conn.write_input_prompt()

            # server tick goes on a timer, use the web server timeout to wait for a limited time
            # wait_time = max(0.01, self.config.server_tick_time - loop_duration)
            self.mud_wsgi_server.timeout = 0.1      # keep things responsive
            self.mud_wsgi_server.handle_request()   # @todo should the wsgi server perhaps run in its own thread instead just as in IF mode?

            loop_start = time.time()
            for conn in self.all_players.values():
                if conn.player.input_is_available.is_set():
                    conn.need_new_input_prompt = True
                    try:
                        self.__server_loop_process_player_input(conn)
                    except (KeyboardInterrupt, EOFError):
                        continue
                    except errors.StoryCompleted:
                        continue   # can't complete 'story' in mud mode
                    except errors.SessionExit:
                        self.story.goodbye(conn.player)
                    except Exception:
                        txt = "* internal error:\n" + traceback.format_exc()
                        conn.player.tell(txt, format=False)
            # server TICK and pending Actions
            now = time.time()
            if now - previous_server_tick >= self.config.server_tick_time:
                self.__server_tick()
                previous_server_tick = now
            self.__server_loop_process_action_queue()
            loop_duration = time.time() - loop_start
            self.server_loop_durations.append(loop_duration)

    def __server_tick(self):
        """
        Do everything that the server needs to do every tick (timer configurable in story)
        1) game clock
        2) heartbeats
        3) deferreds
        4) write buffered output
        """
        self.game_clock.add_realtime(datetime.timedelta(seconds=self.config.server_tick_time))
        ctx = util.Context(driver=self, clock=self.game_clock, config=self.config, player_connection=mud_context.conn)
        for object in self.heartbeat_objects:
            object.heartbeat(ctx)
        while self.deferreds:
            deferred = None
            with self.deferreds_lock:
                if self.deferreds:
                    deferred = self.deferreds[0]
                    if deferred.due <= self.game_clock.clock:
                        deferred = heapq.heappop(self.deferreds)
                    else:
                        deferred = None
                        break
            if deferred:
                # calling the deferred needs to be outside the lock because it can reschedule a new deferred
                try:
                    deferred(ctx=ctx)  # call the deferred and provide a context object
                except Exception:
                    self.__report_deferred_exception(deferred)
        for conn in self.all_players.values():
            conn.write_output()

    def __report_deferred_exception(self, deferred):
        print("\n* Exception while executing deferred action {0}:".format(deferred), file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        print("(continuing...)", file=sys.stderr)

    def __story_complete_output(self, conn):
        conn.player.tell("\n")
        self.story.completion(conn.player)
        conn.player.tell("\n")
        conn.input_direct("\nPress enter to continue. ")
        conn.player.tell("\n")

    def __process_player_command(self, cmd, conn):
        if not cmd:
            return
        if cmd and cmd[0] in cmds.abbreviations and not cmd[0].isalpha():
            # insert a space to separate the first char such as ' or ?
            cmd = cmd[0] + " " + cmd[1:]
        # check for an abbreviation, replace it with the full verb if present
        _verb, _sep, _rest = cmd.partition(" ")
        if _verb in cmds.abbreviations:
            _verb = cmds.abbreviations[_verb]
            cmd = "".join([_verb, _sep, _rest])

        player = conn.player
        # We pass in all 'external verbs' (non-soul verbs) so it will do the
        # parsing for us even if it's a verb the soul doesn't recognise by itself.
        command_verbs = self.commands.get(player.privileges)
        custom_verbs = set(self.current_custom_verbs(player))
        try:
            if _verb in self.commands.no_soul_parsing:
                # don't use the soul to parse it further
                player.turns += 1
                raise soul.NonSoulVerb(soul.ParseResult(_verb, unparsed=_rest.strip()))
            else:
                # Parse the command by using the soul.
                all_verbs = set(command_verbs) | custom_verbs
                parsed = player.parse(cmd, external_verbs=all_verbs)
            # If parsing went without errors, it's a soul verb, handle it as a socialize action
            player.turns += 1
            player.do_socialize_cmd(parsed)
        except soul.NonSoulVerb as x:
            parsed = x.parsed
            if parsed.qualifier:
                # for now, qualifiers are only supported on soul-verbs (emotes).
                raise errors.ParseError("That action doesn't support qualifiers.")
            # Execute non-soul verb. First try directions, then the rest.
            player.turns += 1
            try:
                # Check if the verb is a custom verb and try to handle that.
                # If it remains unhandled, check if it is a normal verb, and handle that.
                # If it's not a normal verb, abort with "please be more specific".
                parse_error = "That doesn't make much sense."
                handled = False
                if parsed.verb in custom_verbs:
                    handled = player.location.handle_verb(parsed, player)
                    if handled:
                        self.after_player_action(lambda: player.location.notify_action(parsed, player))
                    else:
                        parse_error = "Please be more specific."
                if not handled:
                    if parsed.verb in player.location.exits:
                        self.__go_through_exit(player, parsed.verb)
                    elif parsed.verb in command_verbs:
                        func = command_verbs[parsed.verb]
                        ctx = util.Context(driver=self, config=self.config, clock=self.game_clock, player_connection=conn)
                        func(player, parsed, ctx)
                        if func.enable_notify_action:
                            self.after_player_action(lambda: player.location.notify_action(parsed, player))
                    else:
                        raise errors.ParseError(parse_error)
            except errors.RetrySoulVerb:
                # cmd decided it can't deal with the parsed stuff and that it needs to be retried as soul emote.
                player.validate_socialize_targets(parsed)
                player.do_socialize_cmd(parsed)
            except errors.RetryParse as x:
                return self.__process_player_command(x.command, conn)   # try again but with new command string

    def __go_through_exit(self, player, direction):
        exit = player.location.exits[direction]
        exit.allow_passage(player)
        player.move(exit.target)
        player.look()

    def __lookup_location(self, location_name):
        location = self.zones
        modulename = "zones"
        for name in location_name.split('.'):
            if hasattr(location, name):
                location = getattr(location, name)
            else:
                modulename = modulename + "." + name
                __import__(modulename)
                location = getattr(location, name)
        return location

    def __load_saved_game(self):
        assert self.config.server_mode == "if", "games can only be loaded in single player 'if' mode"
        try:
            savegame = self.user_resources[self.config.name.lower() + ".savegame"].data
            state = pickle.loads(savegame)
            del savegame
        except (pickle.PickleError, ValueError, TypeError) as x:
            print("There was a problem loading the saved game data:")
            print(type(x).__name__, x)
            self._stop_driver()
            raise SystemExit(10)
        except IOError:
            print("No saved game data found.")
            return None
        else:
            if state["version"] != self.config.version:
                print("This saved game data was from a different version of the game and cannot be used.")
                print("(Current game version: %s  Saved game data version: %s)" % (self.config.version, state["version"]))
                self._stop_driver()
                raise SystemExit(10)
            # Because loading a complete saved game is strictly for single player 'if' mode,
            # we load a new player and simply replace all players with this one.
            player = state["player"]
            mud_context.player = player
            self.all_players = {player.name: mud_context.conn}
            self.deferreds = state["deferreds"]
            self.game_clock = state["clock"]
            self.heartbeat_objects = state["heartbeats"]
            self.config = state["config"]
            player.tell("\n")
            player.tell("Game loaded.")
            if self.config.display_gametime:
                player.tell("Game time:", self.game_clock)
            player.tell("\n")
            return player

    def current_custom_verbs(self, player):
        """returns dict of the currently recognised custom verbs (verb->helptext mapping)"""
        verbs = player.verbs.copy()
        verbs.update(player.location.verbs)
        for living in player.location.livings:
            verbs.update(living.verbs)
        for item in player.inventory:
            verbs.update(item.verbs)
        for item in player.location.items:
            verbs.update(item.verbs)
        for exit in set(player.location.exits.values()):
            verbs.update(exit.verbs)
        return verbs

    def show_motd(self, player, notify_no_motd=False):
        """Prints the Message-Of-The-Day file, if present. Does nothing in IF mode."""
        try:
            motd = self.resources["messages/motd.txt"]
            message = motd.data.rstrip()
        except IOError:
            message = None
        if message:
            player.tell("<bright>Message-of-the-day:</>", end=True)
            player.tell("\n")
            player.tell(message, end=True, format=True)  # for now, the motd is displayed *with* formatting
            player.tell("\n")
            player.tell("\n")
        elif notify_no_motd:
            player.tell("There's currently no message-of-the-day.")

    def search_player(self, name):
        """
        Look through all the logged in players for one with the given name.
        Returns None if no one is known with that name.
        """
        conn = self.all_players.get(name)
        return conn.player if conn else None

    def get_current_verbs(self, player):
        """return a dict of all currently recognised verbs, and their help text"""
        normal_verbs = self.commands.get(player.privileges)
        verbs = {v: (f.__doc__ or "") for v, f in normal_verbs.items()}
        verbs.update(self.current_custom_verbs(player))
        return verbs

    def do_wait(self, duration):
        # let time pass, duration is in game time (not real time).
        # We do let the game tick for the correct number of times.
        # @todo be able to detect if something happened during the wait
        assert self.config.server_mode == "if"
        if self.config.gametime_to_realtime == 0:
            # game is running with a 'frozen' clock
            # simply advance the clock, and perform a single server_tick
            self.game_clock.add_gametime(duration)
            self.__server_tick()
            return True, None      # uneventful
        num_ticks = int(duration.seconds / self.config.gametime_to_realtime / self.config.server_tick_time)
        if num_ticks < 1:
            return False, "It's no use waiting such a short while."
        for _ in range(num_ticks):
            self.__server_tick()
        return True, None     # wait was uneventful. (@todo return False if something happened)

    def do_save(self, player):
        if not self.config.savegames_enabled:
            player.tell("It is not possible to save your progress.")
            return
        state = {
            "version": self.config.version,
            "player": player,
            "deferreds": self.deferreds,
            "clock": self.game_clock,
            "heartbeats": self.heartbeat_objects,
            "config": self.config
        }
        savedata = pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
        self.user_resources[self.config.name.lower() + ".savegame"] = savedata
        player.tell("Game saved.")
        if self.config.display_gametime:
            player.tell("Game time:", self.game_clock)
        player.tell("\n")

    def register_heartbeat(self, mudobj):
        self.heartbeat_objects.add(mudobj)

    def unregister_heartbeat(self, mudobj):
        self.heartbeat_objects.discard(mudobj)

    def register_exit(self, exit):
        if not exit.bound:
            self.unbound_exits.append(exit)

    def defer(self, due, action, *vargs, **kwargs):
        """
        Register a deferred callable action (optionally with arguments).
        The vargs and the kwargs all must be serializable.
        Note that the due time is datetime.datetime *in game time* (not real time!)
        when the deferred should trigger. It can also be a number, meaning the number
        of real-time seconds after the current time.
        Also note that the deferred *always* gets a kwarg 'ctx' set to a Context object.
        This is often useful, for instance you can register a new deferred on the
        ctx.driver without having to access a global driver object.
        """
        assert callable(action)
        if isinstance(due, datetime.datetime):
            assert due >= self.game_clock.clock
        else:
            due = float(due)
            assert due >= 0.0
            due = self.game_clock.plus_realtime(datetime.timedelta(seconds=due))
        deferred = Deferred(due, action, vargs, kwargs)
        with self.deferreds_lock:
            heapq.heappush(self.deferreds, deferred)

    def after_player_action(self, action):
        """
        Register a callable action in the queue to be called later,
        but directly *after* the player's own actions have been completed.
        """
        self.action_queue.put(action)

    def remove_deferreds(self, owner):
        with self.deferreds_lock:
            self.deferreds = [d for d in self.deferreds if d.owner is not owner]
            heapq.heapify(self.deferreds)

    @property
    def uptime(self):
        """gives the server uptime in a (hours, minutes, seconds) tuple"""
        realtime = datetime.datetime.now()
        realtime = realtime.replace(microsecond=0)
        uptime = realtime - self.server_started
        hours, seconds = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(seconds, 60)
        return hours, minutes, seconds


class StoryConfig(object):
    """Container for the configuration settings for a Story"""
    config_items = {
        "name",
        "author",
        "author_address",
        "version",
        "requires_tale",
        "supported_modes",
        "player_name",
        "player_gender",
        "player_race",
        "money_type",
        "server_tick_method",
        "server_tick_time",
        "gametime_to_realtime",
        "max_wait_hours",
        "display_gametime",
        "epoch",
        "startlocation_player",
        "startlocation_wizard",
        "savegames_enabled",
        "license_file"
    }

    def __init__(self, **kwargs):
        difference = self.config_items ^ set(kwargs)
        if difference:
            raise ValueError("invalid story config; mismatch in config arguments: "+str(difference))
        for k, v in kwargs.items():
            if k in self.config_items:
                setattr(self, k, v)
            else:
                raise AttributeError("unrecognised config attribute: " + k)

    def __eq__(self, other):
        return vars(self) == vars(other)

    @staticmethod
    def copy_from(config):
        assert isinstance(config, StoryConfig)
        return StoryConfig(**vars(config))


if __name__ == "__main__":
    print("Use module tale.main instead.")
    raise SystemExit(1)
