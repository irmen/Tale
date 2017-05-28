"""
Single user driver (for interactive fiction).

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import sys
import time
import threading
import pickle
from typing import Generator, Optional
from .story import GameMode, TickMethod
from . import charbuilder
from . import driver
from . import errors
from . import lang
from . import pubsub
from . import util
from .player import PlayerConnection, Player
from .tio import DEFAULT_SCREEN_DELAY
from .tio import iobase


class IFDriver(driver.Driver):
    """
    The Single user 'driver'.
    Used to control interactive fiction where there's only one 'player'.
    """
    def __init__(self, *, screen_delay: int=DEFAULT_SCREEN_DELAY, gui: bool=False, web: bool=False, wizard_override: bool=False) -> None:
        super().__init__()
        self.game_mode = GameMode.IF
        if screen_delay < 0 or screen_delay > 100:
            raise ValueError("invalid delay, valid range is 0-100")
        self.screen_delay = screen_delay
        self.io_type = "console"
        if gui:
            self.io_type = "gui"
        if web:
            self.io_type = "web"
        self.wizard_override = wizard_override

    def start_main_loop(self):
        if self.io_type == "web":
            print("starting '{0}'  v {1}".format(self.story.config.name, self.story.config.version))
            if self.story.config.author_address:
                print("written by {0} - {1}".format(self.story.config.author, self.story.config.author_address))
            else:
                print("written by", self.story.config.author)
        connection = self.connect_player(self.io_type, self.screen_delay)
        if self.wizard_override:
            connection.player.privileges.add("wizard")
        # create the login dialog
        driver.topic_async_dialogs.send((connection, self._login_dialog_if(connection)))
        # the driver mainloop runs in a background thread, the io-loop/gui-event-loop runs in the main thread
        driver_thread = threading.Thread(name="driver", target=self._main_loop_wrapper, args=(connection,))
        driver_thread.daemon = True
        driver_thread.start()
        connection.singleplayer_mainloop()     # this doesn't return!

    def show_motd(self, player: Player, notify_no_motd: bool=False) -> None:
        pass   # no motd in IF mode

    def do_save(self, player: Player) -> None:
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

    def connect_player(self, player_io_type: str, line_delay: int) -> PlayerConnection:
        connection = PlayerConnection()
        connect_name = "<connecting_%d>" % id(connection)  # unique temporary name
        new_player = Player(connect_name, "n", "elemental", "This player is still connecting to the game.")
        io = None  # type: iobase.IoAdapterBase
        if player_io_type == "gui":
            from .tio.tkinter_io import TkinterIo
            io = TkinterIo(self.story.config, connection)
        elif player_io_type == "web":
            from .tio.if_browser_io import HttpIo, TaleWsgiApp
            wsgi_server = TaleWsgiApp.create_app_server(self, connection)
            io = HttpIo(connection, wsgi_server)
        elif player_io_type == "console":
            from .tio.console_io import ConsoleIo
            io = ConsoleIo(connection)
            io.install_tab_completion(self)
        else:
            raise ValueError("invalid io type, must be one of: gui web console")
        connection.player = new_player
        connection.io = io
        self.all_players[new_player.name] = connection
        new_player.output_line_delay = line_delay
        connection.clear_screen()
        self.print_game_intro(connection)
        return connection

    def _login_dialog_if(self, conn: PlayerConnection) -> Generator:
        # Interactive fiction (singleplayer): create a player. This is a generator function (async input).
        # Initialize it directly from the story's configuration, load a saved game,
        # or let the user create a new player manually.
        # Be sure to always reference conn.player here (and not get a cached copy),
        # because it will get replaced when loading a saved game!
        if not self.story.config.savegames_enabled:
            load_saved_game = False
        else:
            conn.player.tell("\n")
            load_saved_game = yield "input", ("Do you want to load a saved game ('<bright>n</>' will start a new game)?", lang.yesno)
        conn.player.tell("\n")
        if load_saved_game:
            loaded_player = self._load_saved_game(conn.player)
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
        else:
            # No story player config: create a character with the builder
            # This is unusual though, normally any 'if' story should provide a player config
            builder = charbuilder.IFCharacterBuilder(conn)
            name_info = yield from builder.build_character()
            if not name_info:
                raise errors.TaleError("should have a name now")

        player = conn.player
        self._rename_player(player, name_info)
        player.tell("\n")
        # move the player to the starting location:
        if "wizard" in player.privileges:
            player.move(self.lookup_location(self.story.config.startlocation_wizard))
        else:
            player.move(self.lookup_location(self.story.config.startlocation_player))
        player.tell("\n")
        prompt = self.story.welcome(player)
        if prompt:
            conn.input_direct("\n" + prompt)   # blocks  (note: cannot use yield here)
        player.tell("\n")
        self.story.init_player(player)
        player.look(short=False)  # force a 'look' command to get our bearings
        conn.write_output()

    def disconnect_idling(self, conn: PlayerConnection):
        pass

    def disconnect_player(self, conn: PlayerConnection):
        raise errors.TaleError("Disconnecting a player should not happen in single player IF mode. Please report this bug.")

    def main_loop(self, conn: PlayerConnection) -> None:
        """
        The game loop, for the single player Interactive Fiction game mode.
        Until the game is exited, it processes player input, and prints the resulting output.
        """
        conn.write_output()
        loop_duration = 0.0
        previous_server_tick = 0.0

        def story_completed():
            self._stop_mainloop = True
            conn.player.tell("\n")
            conn.input_direct("\n\nPress enter to exit. ")  # blocking
            conn.player.tell("\n")
            self._stop_driver()

        while not self._stop_mainloop:
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
                        self._continue_dialog(conn, dialog, response)
                    else:
                        # normal command processing
                        self._server_loop_process_player_input(conn)
                except (KeyboardInterrupt, EOFError):
                    continue
                except errors.SessionExit:
                    self._stop_mainloop = True
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
                    self._server_tick()
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

    def _load_saved_game(self, player: Player) -> Optional[Player]:
        # at this time, game loading/saving is only supported in single player IF mode.
        # @todo fix that all mudobjects are duplicated when loading a pickle save game.
        assert len(self.all_players) == 1
        conn = list(self.all_players.values())[0]
        try:
            savegame = self.user_resources[util.storyname_to_filename(self.story.config.name) + ".savegame"].data
            state = pickle.loads(savegame)
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
