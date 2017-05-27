"""
Mud driver (server).

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import collections
import datetime
import heapq
import importlib
import inspect
import os
import pathlib
import pickle
import pkgutil
import random
import sys
import threading
import time
from functools import total_ordering
from types import ModuleType
from typing import Sequence, Union, Tuple, Any, Dict, Callable, Iterable, Generator, Set, List, MutableSequence, Optional

import appdirs

from . import __version__ as tale_version_str
from . import mud_context, errors, util, cmds, player, base, pubsub, charbuilder, lang, races, accounts, verbdefs, vfs
from .base import Stats, Living, Location, Exit
from .parseresult import ParseResult
from .story import TickMethod, GameMode, MoneyType, StoryBase
from .tio import DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_DELAY, iobase

topic_pending_actions = pubsub.topic("driver-pending-actions")
topic_pending_tells = pubsub.topic("driver-pending-tells")
topic_async_dialogs = pubsub.topic("driver-async-dialogs")


@total_ordering
class Deferred:
    """
    Represents a callable action that will be invoked (with the given arguments) sometime in the future.
    This object captures the action that must be invoked in a way that is serializable.
    That means that you can't pass all types of callables, there are a few that are not
    serializable (lambda's and scoped functions). They will trigger an error if you use those.
    If you set a (low_seconds, high_seconds) periodical tuple, the deferred will be called periodically
    where the next trigger time is randomized within the given interval.
    The due time is given in Game Time, not in real/wall time!
    """
    def __init__(self, due_gametime: datetime.datetime, action: Callable, vargs: Sequence[Any], kwargs: Dict[str, Any],
                 *, periodical: Tuple[float, float]=None) -> None:
        assert isinstance(due_gametime, datetime.datetime)
        assert callable(action)
        if periodical:
            if not len(periodical) == 2:
                raise ValueError("periodical arg must be None or a tuple(float,float)")
            if periodical[0] < 0.1 or periodical[1] < 0.1:
                raise ValueError("periodial interval values must be > 0.1")
        self.due_gametime = due_gametime   # in game time
        self.owner = getattr(action, "__self__", None)
        if isinstance(self.owner, ModuleType):
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
        self.periodical = periodical

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return self.due_gametime == other.due_gametime and type(self.owner) == type(other.owner)\
                and self.action == other.action and self.vargs == other.vargs and self.kwargs == other.kwargs
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ == other.__class__:
            return self.due_gametime < other.due_gametime   # deferreds must be sortable
        return NotImplemented

    def when_due(self, game_clock: util.GameDateTime, realtime: bool=False) -> datetime.timedelta:
        """
        In what time is this deferred due to occur? (timedelta)
        Normally it is in terms of game-time, but if you pass realtime=True,
        you will get the real-time timedelta.
        """
        secs = (self.due_gametime - game_clock.clock).total_seconds()
        if realtime:
            secs = int(secs / game_clock.times_realtime)
        return datetime.timedelta(seconds=secs)

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        self.kwargs = self.kwargs or {}
        if callable(self.action):
            func = self.action
        else:
            # deferred action is stored as the name of the function to call,
            # so we need to obtain the actual function from the owner object.
            if isinstance(self.owner, str):
                if self.owner.startswith("module:"):
                    # the owner refers to a module
                    self.owner = sys.modules[self.owner[7:]]
                else:
                    raise RuntimeError("invalid owner specifier: " + self.owner)
            func = getattr(self.owner, self.action)
        if "ctx" in inspect.signature(func).parameters:
            self.kwargs["ctx"] = kwargs["ctx"]  # add a 'ctx' keyword argument to the call for convenience
        func(*self.vargs, **self.kwargs)
        if self.periodical:
            # reschedule the same call!
            assert self.periodical[0] > 0 and self.periodical[1] > 0
            due = random.uniform(self.periodical[0], self.periodical[1])
            self.due_gametime = mud_context.driver.game_clock.plus_realtime(datetime.timedelta(seconds=due))
            mud_context.driver._enqueue_deferred(self)  # reschedule!
            # note: when owner is deleted/destroyed, it must make sure that any deferreds from it are removed from the queue!
        else:
            # our lifetime has ended, remove references asap:
            del self.owner
            del self.action
            del self.kwargs
            del self.vargs


class Driver(pubsub.Listener):
    """
    The Mud 'driver'.
    Reads story file and config, initializes game state.
    Handles main game loop, player connections, and loading/saving of game state.
    """
    def __init__(self) -> None:
        self.unbound_exits = []    # type: List[Exit]
        self.deferreds = []   # type: List[Deferred]  # heapq
        self.deferreds_lock = threading.Lock()
        self.server_started = datetime.datetime.now().replace(microsecond=0)
        self.server_loop_durations = collections.deque(maxlen=10)    # type: MutableSequence[float]
        self.commands = Commands()
        self.all_players = {}   # type: Dict[str, player.PlayerConnection]  # maps playername to player connection object
        self.zones = None       # type: ModuleType
        self.moneyfmt = None    # type: util.MoneyFormatter
        self.resources = None   # type: vfs.VirtualFileSystem
        self.user_resources = None  # type: vfs.VirtualFileSystem
        self.story = None   # type: StoryBase
        self.game_clock = None    # type: util.GameDateTime
        self.__stop_mainloop = True
        # playerconnections that wait for input; maps connection to tuple (dialog, validator, echo_input)
        self.waiting_for_input = {}   # type: Dict[player.PlayerConnection, Tuple[Generator, Any, Any]]
        mud_context.driver = self
        for verb, func, privilege in cmds.all_registered_commands():
            self.commands.add(verb, func, privilege)
        cmds.clear_registered_commands()
        topic_pending_actions.subscribe(self)
        topic_pending_tells.subscribe(self)
        topic_async_dialogs.subscribe(self)

    def start(self, game: str, mode: GameMode=GameMode.IF, gui: bool=False, web: bool=False,
              wizard: bool=False, delay: int=DEFAULT_SCREEN_DELAY) -> None:
        """Start the driver from a parsed set of arguments"""
        gamepath = pathlib.Path(game)
        if gamepath.is_dir():
            # cd into the game directory (we can import it then), and load its config and zones
            os.chdir(str(gamepath))
            sys.path.insert(0, os.curdir)
        elif gamepath.is_file():
            # the game argument points to a file, assume it is a zipfile, add it to the import path
            sys.path.insert(0, str(gamepath))
        else:
            raise FileNotFoundError("Cannot find specified game")
        mode = GameMode(mode)
        assert "story" not in sys.modules, "cannot start new story if it was already loaded before"
        import story
        if not hasattr(story, "Story"):
            raise AttributeError("Story class not found in the story file. It should be called 'Story'.")
        self.story = story.Story()
        self.story._verify(self)
        if mode not in self.story.config.supported_modes:
            raise ValueError("driver mode '%s' not supported by this story. Valid modes: %s" %
                             (mode, list(self.story.config.supported_modes)))
        self.story.config.mud_host = self.story.config.mud_host or "localhost"
        self.story.config.mud_port = self.story.config.mud_port or 8180
        self.story.config.server_mode = mode  # if/mud driver mode ('if' = single player interactive fiction, 'mud'=multiplayer)
        if self.story.config.server_mode != GameMode.IF and self.story.config.server_tick_method == TickMethod.COMMAND:
            raise ValueError("'command' tick method can only be used in 'if' game mode")
        # Register the driver and add some more stuff in the global context.
        self.resources = vfs.VirtualFileSystem(root_package="story")   # read-only story resources
        mud_context.config = self.story.config
        mud_context.resources = self.resources
        # check for existence of cmds package in the story root
        loader = pkgutil.get_loader("cmds")
        if loader:
            ld = pathlib.Path(loader.get_filename("cmds")).parent.parent.resolve()        # type: ignore
            sd = pathlib.Path(inspect.getabsfile(story)).parent       # type: ignore   # mypy doesn't recognise getabsfile?
            if ld == sd:   # only load them if the directory is the same as where the story was loaded from
                cmds.clear_registered_commands()   # making room for the story's commands
                # noinspection PyUnresolvedReferences
                import cmds as story_cmds      # import the cmd package from the story
                for verb, func, privilege in cmds.all_registered_commands():
                    try:
                        self.commands.add(verb, func, privilege)
                    except ValueError:
                        self.commands.override(verb, func, privilege)
                cmds.clear_registered_commands()
        self.commands.adjust_available_commands(self.story.config.server_mode)
        self.game_clock = util.GameDateTime(self.story.config.epoch or self.server_started, self.story.config.gametime_to_realtime)
        self.moneyfmt = None
        if self.story.config.money_type != MoneyType.NOTHING:
            self.moneyfmt = util.MoneyFormatter(self.story.config.money_type)
        user_data_dir = pathlib.Path(appdirs.user_data_dir("Tale-" + util.storyname_to_filename(self.story.config.name),
                                                           "Razorvine", roaming=True))
        user_data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.user_resources = vfs.VirtualFileSystem(root_path=user_data_dir, readonly=False)  # r/w to the local 'user data' directory
        self.story.init(self)
        self.zones = self.__load_zones(self.story.config.zones)
        self._lookup_location(self.story.config.startlocation_player)
        self._lookup_location(self.story.config.startlocation_wizard)
        if self.story.config.server_tick_method == TickMethod.COMMAND:
            # If the server tick is synchronized with player commands, this factor needs to be 1,
            # because at every command entered the game time simply advances 1 x server_tick_time.
            self.story.config.gametime_to_realtime = 1
        assert self.story.config.server_tick_time > 0
        assert self.story.config.max_wait_hours >= 0
        self.game_clock = util.GameDateTime(self.story.config.epoch or self.server_started, self.story.config.gametime_to_realtime)
        # convert textual exit strings to actual exit object bindings
        for x in self.unbound_exits:
            x._bind_target(self.zones)
        self.unbound_exits = []
        if delay < 0 or delay > 100:
            raise ValueError("invalid delay, valid range is 0-100")
        sys.excepthook = util.excepthook  # install custom verbose crash reporter
        if self.story.config.server_mode == GameMode.IF:
            # create the single player mode player automatically
            if gui:
                player_io = "gui"
            elif web:
                player_io = "web"
                print("starting '{0}'  v {1}".format(self.story.config.name, self.story.config.version))
                if self.story.config.author_address:
                    print("written by {0} - {1}".format(self.story.config.author, self.story.config.author_address))
                else:
                    print("written by", self.story.config.author)
            else:
                player_io = "console"
            connection = self._connect_if_player(player_io, delay, wizard)
            # create the login dialog
            topic_async_dialogs.send((connection, self.__login_dialog_if(connection)))
            # the driver mainloop runs in a background thread, the io-loop/gui-event-loop runs in the main thread
            driver_thread = threading.Thread(name="driver", target=self.__startup_main_loop, args=(connection,))
            driver_thread.daemon = True
            driver_thread.start()
            connection.singleplayer_mainloop()
        else:
            # mud mode: driver runs as main thread, wsgi webserver runs in background thread
            base._limbo.init_inventory([LimboReaper()])  # add the grim reaper to Limbo
            self.mud_accounts = accounts.MudAccounts()
            from .tio.mud_browser_io import TaleMudWsgiApp
            wsgi_server = TaleMudWsgiApp.create_app_server(self)
            wsgi_thread = threading.Thread(name="wsgi", target=wsgi_server.serve_forever)       # type: ignore
            wsgi_thread.daemon = True
            wsgi_thread.start()
            self.__print_game_intro(None)
            print("Access the game on this web server url:   http://%s:%d/tale/" % wsgi_server.server_address, end="\n\n")   # type: ignore
            self.__startup_main_loop(None)

    def __startup_main_loop(self, conn: player.PlayerConnection) -> None:
        # Kick off the appropriate driver main event loop.
        # This may or may not run in a background thread depending on the driver mode.
        self.__stop_mainloop = False
        num_critical_errors = 0
        time_of_last_critical_error = 0.0
        while not self.__stop_mainloop:
            try:
                if self.story.config.server_mode == GameMode.IF:
                    # single player interactive fiction event loop
                    while not self.__stop_mainloop:
                        self.__main_loop_singleplayer(conn)
                else:
                    # multi player mud event loop
                    while not self.__stop_mainloop:
                        self.__main_loop_multiplayer()
            except KeyboardInterrupt:
                # a ctrl-c will exit the server
                print("* break - stopping server loop")
                if self.all_players:
                    print("  %d players are connected: %s" % (len(self.all_players), "; ".join(self.all_players)))
                self.__stop_mainloop = lang.yesno(input("Are you sure you want to exit the Tale driver? "))
            except Exception:
                # other exceptions are logged but don't break the server loop (hopefully the game can continue)
                # @todo only print it to the player that caused the error (if possible) + to the error log
                num_critical_errors += 1
                last, time_of_last_critical_error = time_of_last_critical_error, time.time()
                if time_of_last_critical_error - last > 1.0:
                    num_critical_errors = 1  # reset critical error count due to low frequency
                if num_critical_errors > 10:
                    msg = "aborting driver main loop due to excessive number of critical errors"
                    sys.stderr.write(msg + "\n\n")
                    self._stop_driver()
                    raise errors.TaleError(msg)
                print("ERROR IN DRIVER MAINLOOP:\n", "".join(util.format_traceback()), file=sys.stderr)
                for conn in self.all_players.values():
                    conn.critical_error()

    def _connect_if_player(self, player_io: str, line_delay: int, wizard_override: bool) -> player.PlayerConnection:
        connection = player.PlayerConnection()
        connect_name = "<connecting_%d>" % id(connection)  # unique temporary name
        new_player = player.Player(connect_name, "n", "elemental", "This player is still connecting to the game.")
        io = None   # type: iobase.IoAdapterBase
        if player_io == "gui":
            from .tio.tkinter_io import TkinterIo
            io = TkinterIo(self.story.config, connection)
        elif player_io == "web":
            from .tio.if_browser_io import HttpIo, TaleWsgiApp
            wsgi_server = TaleWsgiApp.create_app_server(self, connection)
            io = HttpIo(connection, wsgi_server)
        elif player_io == "console":
            from .tio.console_io import ConsoleIo
            io = ConsoleIo(connection)
            io.install_tab_completion(self)
        else:
            raise ValueError("invalid io type, must be one of: gui web console")
        if wizard_override:
            new_player.privileges.add("wizard")
        connection.player = new_player
        connection.io = io
        self.all_players[new_player.name] = connection
        new_player.output_line_delay = line_delay
        connection.clear_screen()
        self.__print_game_intro(connection)
        return connection

    def _connect_mud_player(self) -> player.PlayerConnection:
        connection = player.PlayerConnection()
        connect_name = "<connecting_%d>" % id(connection)  # unique temporary name
        new_player = player.Player(connect_name, "n", "elemental", "This player is still connecting to the game.")
        connection.player = new_player
        from .tio.mud_browser_io import MudHttpIo
        connection.io = MudHttpIo(connection)
        self.all_players[new_player.name] = connection
        connection.clear_screen()
        self.__print_game_intro(connection)
        connection.output("\n")
        # check if we have at least 1 admin user
        if len(self.mud_accounts.all_accounts(having_privilege="wizard")) == 0:
            # there is no wizard, create a dialog to construct the initial admin user
            topic_async_dialogs.send((connection, self.__login_dialog_mud_create_admin(connection)))
            return connection
        # create the login dialog
        topic_async_dialogs.send((connection, self.__login_dialog_mud(connection)))
        return connection

    def _disconnect_mud_player(self, conn_or_player: Union[player.PlayerConnection, player.Player]) -> None:
        # note: conn can be corrupt/disconnected. conn.player, conn.io or conn.player.location can be None.
        if isinstance(conn_or_player, player.PlayerConnection):
            name = conn_or_player.player.name
            conn = conn_or_player
        elif isinstance(conn_or_player, player.Player):
            name = conn_or_player.name
            conn = self.all_players[name]
        else:
            raise TypeError("connection or player object expected")
        assert self.all_players[name] is conn
        if conn.player.location:
            conn.player.tell_others("{Title} suddenly shimmers and fades from sight. %s left the game."
                                    % lang.capital(conn.player.subjective))
        del self.all_players[name]
        conn.write_output()
        # wait a bit to allow the player's screen to display the last goodbye message before killing the connection
        self.defer(1, conn.destroy)

    def __login_dialog_mud_create_admin(self, conn: player.PlayerConnection) -> Generator:
        assert self.story.config.server_mode == GameMode.MUD
        conn.write_output()
        conn.output("<bright>Welcome. There is no admin user registered. "
                    "You'll have to create the initial admin user to be able to start the mud.</>")
        while True:
            conn.output("Creating new admin user.")
            name = yield "input-noecho", ("Please type in the admin's player name.", accounts.MudAccounts.accept_name)
            password = yield "input-noecho", ("Please type in the admin password.", accounts.MudAccounts.accept_password)
            email = yield "input", ("Please type in the admin's email address.", accounts.MudAccounts.accept_email)
            conn.output("You can choose one of the following races: ", lang.join(races.playable_races))
            race = yield "input", ("Player race?", charbuilder.valid_playable_race)
            gender = yield "input", ("What is your gender (m/f/n)?", lang.validate_gender)
            # review the account
            conn.player.tell("<bright>Please review your new character.</>", end=True)
            conn.player.tell("<dim> name:</> %s,  <dim>gender:</> %s,  <dim>race:</> %s,  <dim>email:</> %s" %
                             (name, lang.GENDERS[gender], race, email), end=True)
            if not (yield "input", ("You cannot change your name later. Do you want to create this admin account?", lang.yesno)):
                continue
            else:
                break
        stats = Stats.from_race(race, gender=gender[0])
        self.mud_accounts.create(name, password, email, stats, privileges={"wizard"})
        conn.output("\n")
        conn.output("\n")
        topic_async_dialogs.send((conn, self.__login_dialog_mud(conn)))   # continue with the normal login dialog

    def __login_dialog_mud(self, conn: player.PlayerConnection) -> Generator:
        assert self.story.config.server_mode == GameMode.MUD
        conn.write_output()
        conn.output("<bright>Welcome. We would like to know your player name before you can continue.</>")
        conn.output("<dim>If you are not yet known with us, you can simply type in a new name. "
                    "Otherwise use the name you registered with.</>\n")
        conn.output("\n")
        while True:
            name = yield "input-noecho", ("Please type in your player name.", accounts.MudAccounts.accept_name)
            existing_player = self.search_player(name)
            if existing_player:
                conn.player.tell("That player is already logged in elsewhere. Their current location is " + existing_player.location.name)
                conn.player.tell("and their idle time is %d seconds." % existing_player.idle_time)
                if existing_player.idle_time < 30:
                    conn.player.tell("They are still active.")
                    continue
                if not (yield "input", ("Do you want to kick them out and take over?", lang.yesno)):
                    conn.player.tell("Okay, leaving them in peace.")
                    continue
            try:
                self.mud_accounts.get(name)
                password = yield "input-noecho", "Please type in your password."
            except KeyError:
                conn.player.tell("'<player>%s</>' is the name of a new character." % name)
                if not (yield "input", ("Do you want to create a new character with this name?", lang.yesno)):
                    continue
                # self-service account creation
                conn.player.tell("\n")
                conn.player.tell("<ul><bright>New character creation: '%s'.</>" % name, end=True)
                password = yield "input-noecho", ("Please type in the desired password.", accounts.MudAccounts.accept_password)
                email = yield "input", ("Please type in your email address.", accounts.MudAccounts.accept_email)
                gender = yield "input", ("What is the gender of your player character (m/f/n)?", lang.validate_gender)
                conn.player.tell("You can choose one of the following races: " + lang.join(races.playable_races))
                race = yield "input", ("What should be the race of your player character?", charbuilder.valid_playable_race)
                # review the account
                conn.player.tell("<bright>Please review your new character.</>", end=True)
                conn.player.tell("<dim> name:</> %s,  <dim>gender:</> %s,  <dim>race:</> %s" % (name, lang.GENDERS[gender], race), end=True)
                conn.player.tell("<dim> email:</> " + email, end=True)
                if not (yield "input", ("You cannot change your name later. Do you want to create this character?", lang.yesno)):
                    # abort
                    conn.player.tell("Ok, let's get back to the beginning then.", end=True)
                    continue
                stats = Stats.from_race(race, gender=gender[0])
                account = self.mud_accounts.create(name, password, email, stats)
                conn.player.tell("\n<bright>Your new account has been created!</>  It will now be used to log in.", end=True)
                conn.player.tell("\n")
            try:
                self.mud_accounts.valid_password(name, password)
            except ValueError as x:
                conn.output("<it>%s</it>" % x)
                continue
            else:
                account = self.mud_accounts.get(name)
                if existing_player:
                    # take the place of already logged in player (that was disconnected perhaps?)
                    existing_player.tell("\n")
                    existing_player.tell("<it><rev>You are kicked from the game. Your account is now logged in from elsewhere.</>")
                    existing_player.tell("\n")
                    state = existing_player.__getstate__()
                    state["name"] = conn.player.name    # we can only take the real name after existing player has been kicked out
                    existing_player_location = existing_player.location
                    self._disconnect_mud_player(existing_player)
                    ctx = util.Context(self, self.game_clock, self.story.config, None)
                    # mr. Smith move: delete the other player and restore its properties in us
                    existing_player.destroy(ctx)
                    conn.player.__setstate__(state)
                    name_info = charbuilder.PlayerNaming()
                    name_info.money = state["money"]
                    name_info.name = state["name"]
                    name_info.gender = state["gender"]
                    name_info.stats = state["stats"]
                    name_info.name = account.name   # assume the real name now
                    self.__rename_player(conn.player, name_info)
                    conn.output("\n")
                    same_location = conn.player.location is existing_player_location
                    conn.player.move(existing_player_location, silent=same_location)
                    if same_location:
                        conn.player.location.tell("%s appears again. Is %s a different person, you wonder?" %
                                                  (lang.capital(conn.player.title), conn.player.subjective), exclude_living=conn.player)
                else:
                    # log in normally
                    self.mud_accounts.logged_in(name)
                    if account.logged_in:
                        conn.output("Last login: " + str(account.logged_in))
                break
        if not existing_player:
            # for a new login, we need to rename the transitional player object
            # to the proper account name, and move the player to the starting location.
            name_info = charbuilder.PlayerNaming()
            name_info.name = account.name
            name_info.gender = account.stats.gender
            name_info.stats = account.stats
            self.__rename_player(conn.player, name_info)
            conn.player.privileges = account.privileges
            conn.output("\n")
            if "wizard" in conn.player.privileges:
                conn.player.move(self._lookup_location(self.story.config.startlocation_wizard))
            else:
                conn.player.move(self._lookup_location(self.story.config.startlocation_player))
        prompt = self.story.welcome(conn.player)
        if prompt:
            yield "input", "\n" + prompt
        self.story.init_player(conn.player)
        conn.output("\n")
        self.show_motd(conn.player, True)
        conn.player.look(short=False)  # force a 'look' command to get our bearings
        # after this, the generator (dialog) ends and we drop down into the regular command loop

    def _stop_driver(self) -> None:
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

    def __continue_dialog(self, conn: player.PlayerConnection, dialog: Generator, message: str) -> None:
        # Notice that the try...except structure is very similar to
        # the one in __server_loop_process_player_input
        # That's no surprise because also in this async case, we need
        # to handle any parse errors and such that may be thrown from the
        # generator. The reguar player input function has to deal with
        # them as well, caused by normal player commands.
        try:
            why, what = dialog.send(message)
        except StopIteration:
            if conn.player:
                conn.write_output()   # immediately give feedback (if any) once the dialog ends
        except errors.ActionRefused as x:
            conn.player.remember_previous_parse()
            conn.player.tell(str(x))
            conn.write_output()
        except errors.ParseError as x:
            conn.player.tell(str(x))
            conn.write_output()
        else:
            if why in ("input", "input-noecho"):
                if isinstance(what, tuple):
                    prompt, validator = what
                else:
                    prompt, validator = what, None
                if prompt:
                    if not prompt.endswith(" "):
                        prompt += " "
                    conn.write_output()
                    conn.output_no_newline(prompt)  # the input prompt
                assert conn not in self.waiting_for_input, "can only run one async dialog at the same time"
                conn.io.dont_echo_next_cmd = why == "input-noecho"  # this avoids echoing of the password
                self.waiting_for_input[conn] = (dialog, validator, why != "input-noecho")
            else:
                raise ValueError("invalid generator wait reason: " + why)

    def __print_game_intro(self, conn: player.PlayerConnection) -> None:
        try:
            # print game banner as supplied by the game
            banner = self.resources["messages/banner.txt"].text
            if conn:
                conn.player.tell("<bright>%s</>" % banner, format=False)
                conn.player.tell("\n")
            else:
                print(banner)
        except IOError:
            # no banner provided by the game, print default game header
            if conn:
                o = conn.output
                o("")
                o("")
                o("<monospaced><bright>")
                o(("'%s'" % self.story.config.name).center(DEFAULT_SCREEN_WIDTH))
                o(("v" + self.story.config.version).center(DEFAULT_SCREEN_WIDTH))
                o("")
                o(("written by " + self.story.config.author).center(DEFAULT_SCREEN_WIDTH))
                if self.story.config.author_address:
                    o(self.story.config.author_address.center(DEFAULT_SCREEN_WIDTH))
                o("</></monospaced>")
                o("")
                o("")
        if not conn:
            print("\n")
            print("Tale library:", tale_version_str)
            print("MudLib:       %s, v%s" % (self.story.config.name, self.story.config.version))
            if self.story.config.author:
                print("Written by:   %s - %s" % (self.story.config.author, self.story.config.author_address or ""))
            print("Driver start:", time.ctime())
            print("\n")

    def __rename_player(self, player: player.Player, name_info: charbuilder.PlayerNaming) -> None:
        conn = self.all_players[player.name]
        del self.all_players[player.name]
        old_wiretap = player.get_wiretap()
        old_wiretap.destroy()
        self.all_players[name_info.name] = conn
        name_info.apply_to(player)

    def __login_dialog_if(self, conn: player.PlayerConnection) -> Generator:
        # Interactive fiction (singleplayer): create a player. This is a generator function (async input).
        # Initialize it directly from the story's configuration, load a saved game,
        # or let the user create a new player manually.
        # Be sure to always reference conn.player here (and not get a cached copy),
        # because it will get replaced when loading a saved game!
        assert self.story.config.server_mode == GameMode.IF
        if not self.story.config.savegames_enabled:
            load_saved_game = False
        else:
            conn.player.tell("\n")
            load_saved_game = yield "input", ("Do you want to load a saved game ('<bright>n</>' will start a new game)?", lang.yesno)
        conn.player.tell("\n")
        if load_saved_game:
            loaded_player = self.__load_saved_game(conn.player)
            if loaded_player:
                conn.player = loaded_player
                conn.player.tell("\n")
                prompt = self.story.welcome_savegame(conn.player)
                if prompt:
                    yield "input", "\n" + prompt
                conn.player.tell("\n")
            else:
                load_saved_game = False

        if load_saved_game:
            self.story.init_player(conn.player)
            conn.player.look(short=False)   # force a 'look' command to get our bearings
            return

        if self.story.config.player_name:
            # story config provides a name etc.
            name_info = charbuilder.PlayerNaming()
            name_info.name = self.story.config.player_name
            name_info.stats.race = self.story.config.player_race
            name_info.gender = self.story.config.player_gender
            name_info.money = self.story.config.player_money or 0.0
            name_info.wizard = "wizard" in conn.player.privileges
            self.__login_dialog_if_2(conn, name_info)   # finish the login dialog
        else:
            # No story player config: create a character with the builder
            # This is unusual though, normally any 'if' story should provide a player config
            builder = charbuilder.CharacterBuilder(conn, lambda name_info: self.__login_dialog_if_2(conn, name_info))
            topic_async_dialogs.send((conn, builder.build_async()))

    def __login_dialog_if_2(self, conn: player.PlayerConnection, name_info: charbuilder.PlayerNaming) -> None:
        # Second part of the if login dialog, this has been split to be able
        # to put in the character builder dialog that continues with this one.
        player = conn.player
        self.__rename_player(player, name_info)
        player.tell("\n")
        # move the player to the starting location:
        if "wizard" in player.privileges:
            player.move(self._lookup_location(self.story.config.startlocation_wizard))
        else:
            player.move(self._lookup_location(self.story.config.startlocation_player))
        player.tell("\n")
        prompt = self.story.welcome(player)
        if prompt:
            conn.input_direct("\n" + prompt)   # blocks  (note: cannot use yield here)
        player.tell("\n")
        self.story.init_player(player)
        player.look(short=False)  # force a 'look' command to get our bearings
        conn.write_output()

    def __main_loop_singleplayer(self, conn: player.PlayerConnection) -> None:
        """
        The game loop, for the single player Interactive Fiction game mode.
        Until the game is exited, it processes player input, and prints the resulting output.
        """
        conn.write_output()
        loop_duration = 0.0
        previous_server_tick = 0.0

        def story_completed():
            self.__stop_mainloop = True
            conn.player.tell("\n")
            conn.input_direct("\n\nPress enter to exit. ")  # blocking
            conn.player.tell("\n")
            self._stop_driver()

        while not self.__stop_mainloop:
            pubsub.sync("driver-async-dialogs")
            if conn not in self.waiting_for_input:
                conn.write_input_prompt()
            if self.story.config.server_tick_method == TickMethod.COMMAND:
                conn.player.input_is_available.wait()   # blocking wait until playered entered something
                has_input = True
            elif self.story.config.server_tick_method == TickMethod.TIMER:
                # server tick goes on a timer, wait a limited time for player input before going on
                input_wait_time = max(0.01, self.story.config.server_tick_time - loop_duration)
                has_input = conn.player.input_is_available.wait(input_wait_time)
            else:
                raise ValueError("invalid tick method")

            loop_start = time.time()
            if has_input:
                conn.need_new_input_prompt = True
                try:
                    if not conn.player:
                        continue
                    if conn in self.waiting_for_input:
                        # this connection is processing direct input, rather than regular commands
                        dialog, validator, echo_input = self.waiting_for_input.pop(conn)
                        response = conn.player.get_pending_input()[0]
                        if validator:
                            try:
                                response = validator(response)
                            except ValueError as x:
                                prompt = conn.last_output_line
                                conn.io.dont_echo_next_cmd = not echo_input
                                conn.output(str(x) or "That is not a valid answer.")
                                conn.output_no_newline(prompt)   # print the input prompt again
                                self.waiting_for_input[conn] = (dialog, validator, echo_input)   # reschedule
                                continue
                        self.__continue_dialog(conn, dialog, response)
                    else:
                        # normal command processing
                        self.__server_loop_process_player_input(conn)
                except (KeyboardInterrupt, EOFError):
                    continue
                except errors.SessionExit:
                    self.__stop_mainloop = True
                    self.story.goodbye(conn.player)
                    self._stop_driver()
                    break
                except errors.StoryCompleted:
                    story_completed()
                    break
                except Exception:
                    txt = "\n<bright><rev>* internal error (please report this):</>\n" + "".join(util.format_traceback())
                    if conn.player:
                        conn.player.tell(txt, format=False)
                        conn.player.tell("<rev><it>Please report this problem.</>")
                    else:
                        print("ERROR IN SINGLE PLAYER DRIVER LOOP:", file=sys.stderr)
                        print(txt, file=sys.stderr)
                    del txt
            try:
                # sync pubsub pending tells
                pubsub.sync("driver-pending-tells")
                # server TICK
                now = time.time()
                if now - previous_server_tick >= self.story.config.server_tick_time:
                    self.__server_tick()
                    previous_server_tick = now
                if self.story.config.server_tick_method == TickMethod.COMMAND:
                    # Even though the server tick may be skipped, the pubsub events
                    # should be processed every player command no matter what.
                    pubsub.sync()
            except errors.StoryCompleted:
                # completing the story can also be done from a deferred action or pubsub event
                story_completed()
                break
            loop_duration = time.time() - loop_start
            self.server_loop_durations.append(loop_duration)
            conn.write_output()

    def __server_loop_process_player_input(self, conn: player.PlayerConnection) -> None:
        p = conn.player
        assert p.input_is_available.is_set()
        for cmd in p.get_pending_input():
            if not cmd:
                continue
            try:
                p.tell("\n")
                self.__process_player_command(cmd, conn)
                p.remember_previous_parse()
                # to avoid flooding/abuse, we stop the loop after processing one command.
                break
            except errors.UnknownVerbException as x:
                if x.verb in {"north", "east", "south", "west", "northeast", "northwest", "southeast", "southwest",
                              "north east", "north west", "south east", "south west", "up", "down"}:
                    p.tell("You can't go in that direction.")
                else:
                    p.tell("The verb '%s' is unrecognized." % x.verb)
                    if x.verb[0].isupper():
                        p.tell("Just type in lowercase ('%s')." % x.verb.lower())
            except errors.ActionRefused as x:
                p.remember_previous_parse()
                p.tell(str(x))
            except errors.ParseError as x:
                p.tell(str(x))

    def __main_loop_multiplayer(self) -> None:
        """
        The game loop, for the multiplayer MUD mode.
        Until the server is shut down, it processes player input, and prints the resulting output.
        """
        loop_duration = 0.0
        previous_server_tick = 0.0
        while not self.__stop_mainloop:
            pubsub.sync("driver-async-dialogs")
            for conn in self.all_players.values():
                conn.write_output()
                if conn not in self.waiting_for_input:
                    conn.write_input_prompt()

            # server tick goes on a timer
            wait_time = max(0.01, self.story.config.server_tick_time - loop_duration)
            while wait_time > 0:
                if any(conn.player.input_is_available.is_set() for conn in self.all_players.values()):
                    # there was player input, abort the wait loop and deal with it
                    break
                sub_wait = min(0.1, wait_time)  # keep things responsive
                time.sleep(sub_wait)
                wait_time -= sub_wait

            loop_start = time.time()
            for conn in list(self.all_players.values()):
                if conn.player.input_is_available.is_set():
                    conn.need_new_input_prompt = True
                    try:
                        if conn in self.waiting_for_input:
                            # this connection is processing direct input, rather than regular commands
                            dialog, validator, echo_input = self.waiting_for_input.pop(conn)
                            response = conn.player.get_pending_input()[0]
                            if validator:
                                try:
                                    response = validator(response)
                                except ValueError as x:
                                    prompt = conn.last_output_line
                                    conn.io.dont_echo_next_cmd = not echo_input
                                    conn.output(str(x) or "That is not a valid answer.")
                                    conn.output_no_newline(prompt)   # print the input prompt again
                                    self.waiting_for_input[conn] = (dialog, validator, echo_input)   # reschedule
                                    continue
                            self.__continue_dialog(conn, dialog, response)
                        else:
                            # normal command processing
                            self.__server_loop_process_player_input(conn)
                    except (KeyboardInterrupt, EOFError):
                        continue
                    except errors.SessionExit:
                        self.story.goodbye(conn.player)
                        topic_pending_tells.send(lambda conn=conn: self._disconnect_mud_player(conn))
                    except Exception:
                        tb = "".join(util.format_traceback())
                        txt = "\n<bright><rev>* internal error (please report this):</>\n" + tb
                        conn.player.tell(txt, format=False)
                        conn.player.tell("<rev><it>Please report this problem.</>")
            pubsub.sync("driver-pending-tells")
            # server TICK
            now = time.time()
            if now - previous_server_tick >= self.story.config.server_tick_time:
                self.__server_tick()
                previous_server_tick = now
            loop_duration = time.time() - loop_start
            self.server_loop_durations.append(loop_duration)

    def __server_tick(self) -> None:
        """
        Do everything that the server needs to do every tick (timer configurable in story)
        1) game clock
        2) deferreds
        3) pending pubsub events
        4) write buffered output
        5) verify validity and idle state of connected players
        6) remove idle wiretaps
        """
        self.game_clock.add_realtime(datetime.timedelta(seconds=self.story.config.server_tick_time))
        ctx = util.Context(self, self.game_clock, self.story.config, None)
        while self.deferreds:
            deferred = None
            with self.deferreds_lock:
                if self.deferreds:
                    deferred = self.deferreds[0]
                    if deferred.due_gametime <= self.game_clock.clock:
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
        pubsub.sync()
        for name, conn in list(self.all_players.items()):
            if conn.player and conn.io and conn.player.location:
                idle_limit = 3 * 60 * 60 if "wizard" in conn.player.privileges else 30 * 60
                if self.story.config.server_mode == GameMode.MUD and conn.idle_time > idle_limit:
                    idle_limit_minutes = int(idle_limit / 60)
                    conn.player.tell("\n")
                    conn.player.tell("<it><rev>Automatic logout:  You have been logged out because "
                                     "you've been idle for too long (%d minutes)</>" % idle_limit_minutes, end=True)
                    conn.player.tell("\n")
                    conn.player.tell_others("{Title} has been idling around for too long.")
                    self._disconnect_mud_player(conn)   # remove players who stay idle too long
                conn.write_output()
            else:
                # disconnect corrupt player connection
                self._disconnect_mud_player(conn)
        # clean up idle wiretap topics
        topicinfo = pubsub.pending()
        for topicname in topicinfo:
            if isinstance(topicname, tuple) and topicname[0].startswith("wiretap-"):
                events, idle_time, subbers = topicinfo[topicname]
                if events == 0 and not subbers and idle_time > 30:
                    pubsub.topic(topicname).destroy()

    def __report_deferred_exception(self, deferred: Deferred) -> None:
        print("\n* Exception while executing deferred action {0}:".format(deferred), file=sys.stderr)
        print("".join(util.format_traceback()), file=sys.stderr)
        print("(Please report this problem)", file=sys.stderr)

    def __process_player_command(self, cmd: str, conn: player.PlayerConnection) -> None:
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
                raise errors.NonSoulVerb(ParseResult(_verb, unparsed=_rest.strip()))
            else:
                # Parse the command by using the soul.
                all_verbs = set(command_verbs) | custom_verbs
                parsed = player.parse(cmd, external_verbs=all_verbs)
            # If parsing went without errors, it's a soul verb, handle it as a socialize action
            player.turns += 1
            player.do_socialize_cmd(parsed)
        except errors.NonSoulVerb as x:
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
                    # note: can't deal with yields directly, use errors.AsyncDialog in handle_verb to initiate a dialog
                    handled = player.location.handle_verb(parsed, player)
                    if handled:
                        topic_pending_actions.send(lambda actor=player: actor.location.notify_action(parsed, actor))
                    else:
                        parse_error = "Please be more specific."
                if not handled:
                    if parsed.verb in player.location.exits:
                        self._go_through_exit(player, parsed.verb)
                    elif parsed.verb in command_verbs:
                        # Here, one of the commands as annotated with @cmd (or @wizcmd) is executed
                        func = command_verbs[parsed.verb]
                        del command_verbs  # no longer needed
                        ctx = util.Context(self, self.game_clock, self.story.config, conn)
                        if getattr(func, "is_generator", False):
                            dialog = func(player, parsed, ctx)
                            topic_async_dialogs.send((conn, dialog))    # enqueue as async, and continue
                        else:
                            func(player, parsed, ctx)
                        if func.enable_notify_action:   # type: ignore
                            topic_pending_actions.send(lambda actor=player: actor.location.notify_action(parsed, actor))
                    else:
                        raise errors.ParseError(parse_error)
            except errors.RetrySoulVerb:
                # cmd decided it can't deal with the parsed stuff and that it needs to be retried as soul emote.
                player.validate_socialize_targets(parsed)
                player.do_socialize_cmd(parsed)
            except errors.RetryParse as x:
                return self.__process_player_command(x.command, conn)   # try again but with new command string
            except errors.AsyncDialog as x:
                # the player command ended but signaled that an async dialog should be initiated
                topic_async_dialogs.send((conn, x.dialog))

    def _go_through_exit(self, player: player.Player, direction: str) -> None:
        xt = player.location.exits[direction]
        xt.allow_passage(player)
        player.move(xt.target)
        player.look()

    def _lookup_location(self, location_name: str) -> Location:
        location = self.zones
        modulename = "zones"
        for name in location_name.split('.'):
            modulename += "." + name
            if hasattr(location, name):
                location = getattr(location, name)
            else:
                try:
                    module = importlib.import_module(modulename)
                    location = module
                except ImportError:
                    raise errors.TaleError("location not found: " + location_name)
        return location   # type: ignore

    def __load_zones(self, zone_names: Sequence[str]) -> ModuleType:
        # Pre-load the provided zones (essentially, load the named modules from the zones package)
        if not zone_names and "zones" not in sys.modules:
            raise errors.StoryConfigError("story config doesn't provide any zones to load and hasn't loaded any zones itself")
        for zone in zone_names or []:
            try:
                module = importlib.import_module("zones." + zone)
            except ImportError:
                raise errors.TaleError("zone not found: " + zone)
            module.init(self)   # type: ignore
        return importlib.import_module("zones")

    def __load_saved_game(self, player: player.Player) -> Optional[player.Player]:
        # @todo fix that all mudobjects are duplicated when loading a pickle save game.
        assert self.story.config.server_mode == GameMode.IF, "games can only be loaded in single player 'if' mode"
        assert len(self.all_players) == 1
        conn = list(self.all_players.values())[0]
        try:
            savegame = self.user_resources[util.storyname_to_filename(self.story.config.name) + ".savegame"].data
            state = pickle.loads(savegame)   # type: ignore
            del savegame
        except (pickle.PickleError, ValueError, TypeError) as x:
            print("There was a problem loading the saved game data:")
            print(type(x).__name__, x)
            self._stop_driver()
            raise SystemExit(10)
        except IOError:
            player.tell("No saved game data found.", end=True)
            return None
        else:
            if state["version"] != self.story.config.version:
                player.tell("This saved game data was from a different version of the game and cannot be used.")
                player.tell("(Current game version: %s  Saved game data version: %s)" % (self.story.config.version, state["version"]))
                player.tell("\n")
                return None
            # Because loading a complete saved game is strictly for single player 'if' mode,
            # we load a new player and simply replace all players with this one.
            player = state["player"]
            self.all_players = {player.name: conn}
            self.deferreds = state["deferreds"]
            self.game_clock = state["clock"]
            self.story.config = state["config"]
            self.waiting_for_input = {}   # can't keep the old waiters around
            player.tell("\n")
            player.tell("Game loaded.")
            if self.story.config.display_gametime:
                player.tell("Game time: %s" % self.game_clock)
            player.tell("\n")
            return player

    def current_custom_verbs(self, player: player.Player) -> Dict[str, str]:
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

    def current_verbs(self, player: player.Player) -> Dict[str, str]:
        """return a dict of all currently recognised verbs, and their help text"""
        normal_verbs = self.commands.get(player.privileges)
        verbs = {v: (f.__doc__ or "") for v, f in normal_verbs.items()}
        verbs.update(self.current_custom_verbs(player))
        return verbs

    def show_motd(self, player: player.Player, notify_no_motd: bool=False) -> None:
        """Prints the Message-Of-The-Day file, if present. Does nothing in IF mode."""
        try:
            message = self.resources["messages/motd.txt"].text.rstrip()
        except IOError:
            message = None
        if message:
            player.tell("<bright>Message-of-the-day:</>", end=True)
            player.tell("\n")
            player.tell(message, end=True, format=True)  # for now, the motd is displayed *with* formatting
            player.tell("\n")
            player.tell("\n")
        elif notify_no_motd:
            player.tell("There's currently no message-of-the-day.", end=True)
            player.tell("\n")

    def search_player(self, name: str) -> Optional[player.Player]:
        """
        Look through all the logged in players for one with the given name.
        Returns None if no one is known with that name.
        """
        name = name.lower()
        conn = self.all_players.get(name)
        if not conn:
            for pname, conn in self.all_players.items():
                if name == pname.lower():
                    break
            return None
        return conn.player

    def do_wait(self, duration: datetime.timedelta) -> Tuple[bool, Optional[str]]:
        # let time pass, duration is in game time (not real time).
        # We do let the game tick for the correct number of times.
        # @todo be able to detect if something happened during the wait
        assert self.story.config.server_mode == GameMode.IF
        if self.story.config.gametime_to_realtime == 0:
            # game is running with a 'frozen' clock
            # simply advance the clock, and perform a single server_tick
            self.game_clock.add_gametime(duration)
            self.__server_tick()
            return True, None      # uneventful
        num_ticks = int(duration.seconds / self.story.config.gametime_to_realtime / self.story.config.server_tick_time)
        if num_ticks < 1:
            return False, "It's no use waiting such a short while."
        for _ in range(num_ticks):
            self.__server_tick()
        return True, None     # wait was uneventful. (@todo return False if something happened)

    def do_save(self, player: player.Player) -> None:
        if not self.story.config.savegames_enabled:
            player.tell("It is not possible to save your progress.")
            return
        state = {
            "version": self.story.config.version,
            "player": player,
            "deferreds": self.deferreds,
            "clock": self.game_clock,
            "config": self.story.config
        }
        savedata = pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
        self.user_resources[util.storyname_to_filename(self.story.config.name) + ".savegame"] = savedata
        player.tell("Game saved.")
        if self.story.config.display_gametime:
            player.tell("Game time: %s" % self.game_clock)
        player.tell("\n")

    def register_exit(self, exit: Exit) -> None:
        if not exit.target:
            self.unbound_exits.append(exit)

    DeferDueType = Union[datetime.datetime, float, Tuple[float, float, float]]

    def defer(self, due: DeferDueType, action: Callable, *vargs: Any, **kwargs: Any) -> Deferred:
        """
        Register a deferred callable action (optionally with arguments).
        The vargs and the kwargs all must be serializable.
        Note that the due time can be one of:
        -  datetime.datetime *in game time* (not real time!) when the deferred should trigger.
        -  float, meaning the number of real-time seconds after the current time (minimum: 0.1 sec)
        -  tuple(initial_secs, low_secs, high_secs), meaning it is periodical within the given time interval.
        The deferred gets a kwarg 'ctx' set to a Context object, if it has
        a 'ctx' argument in its signature. (If not, that's okay too)
        Receiving the context is often useful, for instance you can register a new
        deferred on the ctx.driver without having to access a global driver object.
        Triggering a deferred can not occur sooner than the server tick period!
        """
        assert callable(action)
        if isinstance(due, datetime.datetime):
            assert due >= self.game_clock.clock
            deferred = Deferred(due, action, vargs, kwargs)
        elif isinstance(due, tuple):
            due, periodical_low, periodical_high = due
            if due < 0.1 or periodical_low < 0.1 or periodical_high < 0.1:
                raise ValueError("due time and periodical times must be >= 0.1  action: %s" % action)
            assert periodical_high >= periodical_low
            due = self.game_clock.plus_realtime(datetime.timedelta(seconds=due))
            deferred = Deferred(due, action, vargs, kwargs, periodical=(periodical_low, periodical_high))
        else:
            due = float(due)
            if due < 0.1:
                raise ValueError("due time must be >= 0.1  action: %s" % action)
            due = self.game_clock.plus_realtime(datetime.timedelta(seconds=due))
            deferred = Deferred(due, action, vargs, kwargs)
        self._enqueue_deferred(deferred)
        return deferred

    def _enqueue_deferred(self, deferred: Deferred) -> None:
        with self.deferreds_lock:
            heapq.heappush(self.deferreds, deferred)

    def pubsub_event(self, topicname: pubsub.TopicNameType, event: Union[Callable, Tuple[player.PlayerConnection, str]]) -> None:
        if topicname == "driver-pending-actions":
            assert callable(event), "the driver-pending-actions events should be callables"
            event()
        elif topicname == "driver-pending-tells":
            assert callable(event), "the driver-pending-tells events should be callables"
            event()
        elif topicname == "driver-async-dialogs":
            assert type(event) is tuple
            conn, dialog = event  # type: ignore
            assert type(conn) is player.PlayerConnection
            assert inspect.isgenerator(dialog)
            self.__continue_dialog(conn, dialog, None)
        else:
            raise ValueError("unknown topic: " + str(topicname))

    def remove_deferreds(self, owner: str) -> None:
        with self.deferreds_lock:
            self.deferreds = [d for d in self.deferreds if d.owner is not owner]
            heapq.heapify(self.deferreds)

    @property
    def uptime(self) -> Tuple[int, int, int]:
        """gives the server uptime in a (hours, minutes, seconds) tuple"""
        realtime = datetime.datetime.now()
        realtime = realtime.replace(microsecond=0)
        uptime = realtime - self.server_started
        hours, seconds = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(seconds, 60)
        return int(hours), int(minutes), int(seconds)


class Commands:
    """
    Some utility functions to manage the registered commands.
    """
    def __init__(self) -> None:
        self.commands_per_priv = {None: {}}    # type: Dict[str, Dict[str, Callable]]
        self.no_soul_parsing = set()   # type: Set[str]

    def add(self, verb: str, func: Callable, privilege: str=None) -> None:
        self.validatefunc(func)
        for commands in self.commands_per_priv.values():
            if verb in commands:
                raise ValueError("command defined more than once: " + verb)
        self.commands_per_priv.setdefault(privilege, {})[verb] = func

    def override(self, verb: str, func: Callable, privilege: str=None) -> Callable:
        self.validatefunc(func)
        if verb in self.commands_per_priv[privilege]:
            existing = self.commands_per_priv[privilege][verb]
            self.commands_per_priv[privilege][verb] = func
            return existing
        raise KeyError("command not defined: " + verb)

    def validatefunc(self, func: Callable) -> None:
        if not hasattr(func, "is_tale_command_func"):
            raise ValueError("the function '%s' is not a proper command function (did you forget the decorator?)" % func.__name__)

    def get(self, privileges: Iterable[str]) -> Dict[str, Callable]:
        result = dict(self.commands_per_priv[None])  # always include the cmds for None
        for priv in privileges:
            if priv in self.commands_per_priv:
                result.update(self.commands_per_priv[priv])
        return result

    def adjust_available_commands(self, server_mode: GameMode) -> None:
        # disable commands flagged with the given game_mode
        # disable soul verbs flagged with override
        # mark non-soul commands
        for commands in self.commands_per_priv.values():
            for cmd, func in list(commands.items()):
                disabled_mode = getattr(func, "disabled_in_mode", None)
                if server_mode == disabled_mode:
                    del commands[cmd]
                elif getattr(func, "overrides_soul", False):
                    del verbdefs.VERBS[cmd]
                if getattr(func, "no_soul_parse", False):
                    self.no_soul_parsing.add(cmd)


class LimboReaper(base.Living):
    """The Grim Reaper hangs about in Limbo, and makes sure no one stays there for too long."""
    def __init__(self) -> None:
        super().__init__(
            "reaper", "m", "elemental", "Grim Reaper",
            description="He wears black robes with a hood. Where a face should be, there is only nothingness. "
                        "He is carrying a large ominous scythe that looks very, very sharp.",
            short_description="A figure clad in black, carrying a scythe, is also present.")
        self.aliases = {"figure", "death"}
        self.candidates = {}    # type: Dict[base.Living, Tuple[float, int]]  # living (usually a player) --> (first_seen, texts shown)

    def notify_action(self, parsed: ParseResult, actor: Living) -> None:
        if parsed.verb == "say":
            actor.tell("%s just stares blankly at you, not saying a word." % lang.capital(self.title))
        else:
            actor.tell("%s stares blankly at you." % lang.capital(self.title))

    @util.call_periodically(3)
    def do_reap_souls(self, ctx: util.Context) -> None:
        # consider all livings currently in Limbo or having their location set to Limbo
        if self.location is not base._limbo:
            # we somehow got misplaced, teleport back to limbo
            self.tell_others("{Title} looks around in wonder and says, \"I'm not supposed to be here.\"")
            self.move(base._limbo, self)
            return
        in_limbo = {living for living in self.location.livings if living is not self}
        in_limbo.update({conn.player for conn in ctx.driver.all_players.values() if conn.player.location is base._limbo})
        now = time.time()
        for candidate in in_limbo:
            if candidate not in self.candidates:
                self.candidates[candidate] = (now, 0)   # a new player first seen
        for candidate in list(self.candidates):
            if candidate not in in_limbo:
                del self.candidates[candidate]   # player no longer present in limbo
                continue
            first_seen, shown = self.candidates[candidate]
            duration = now - first_seen
            # Depending on how long the candidate is being observed, show increasingly threateningly warnings,
            # and eventually killing the candidate (and closing their connection).
            # For wizard players, this is not done and only a short notification is printed.
            if "wizard" in candidate.privileges and duration >= 2 and shown < 1:
                candidate.tell(self.title + " whispers: \"Hello there wizard. Please don't stay for too long.\"")
                shown = 99999
            if duration >= 30 and shown < 1:
                candidate.tell(self.title + " whispers: \"Greetings. Be aware that you must not linger here... Decide swiftly...\"")
                shown = 1
            elif duration >= 50 and shown < 2:
                candidate.tell(self.title + " looms over you and warns: \"You really cannot stay here much longer!\"")
                shown = 2
            elif duration >= 60 and shown < 3:
                candidate.tell(self.title + " menacingly raises his scythe!")
                shown = 3
            elif duration >= 63 and shown < 4:
                candidate.tell(self.title + " swings down his scythe and slices your soul cleanly in half. You are destroyed.")
                shown = 4
            elif duration >= 64 and "wizard" not in candidate.privileges:
                try:
                    conn = ctx.driver.all_players[candidate.name]
                except KeyError:
                    pass   # already gone
                else:
                    ctx.driver._disconnect_mud_player(conn)
            self.candidates[candidate] = (first_seen, shown)


if __name__ == "__main__":
    print("Use module tale.main instead.")
    raise SystemExit(1)
