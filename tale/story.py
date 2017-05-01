"""
Story configuration and base classes to create your own story with.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import enum
import datetime
import distutils.version
from typing import Optional, Any
from tale.errors import StoryConfigError

__all__ = ["TickMethod", "GameMode", "MoneyType", "Storybase"]


class TickMethod(enum.Enum):
    COMMAND = "command"
    TIMER = "timer"


class GameMode(enum.Enum):
    IF = "if"
    MUD = "mud"


class MoneyType(enum.Enum):
    FANTASY = "fantasy"
    MODERN = "modern"
    NOTHING = None  # type: str

    def __bool__(self):
        return bool(self.value)


class Storybase:
    """base class for tale story classes."""
    name = None                     # type: str # the name of the story
    author = None                   # type: str # the story's author name
    author_address = None           # type: str # the author's email address
    version = "1.2"                 # arbitrary but is used to check savegames for compatibility
    requires_tale = "3.0"           # tale library required to run the game
    supported_modes = {GameMode.IF}    # what driver modes (if/mud) are supported by this story
    player_name = None              # type: str # set a name to create a prebuilt player, None to use the character builder
    player_gender = None            # type: str # m/f/n
    player_race = None              # type: str # default is "human" ofcourse, but you can select something else if you want
    player_money = 0.0              # starting money
    money_type = None               # type: MoneyType # money type modern/fantasy/nothing(=None)
    server_tick_method = TickMethod.COMMAND   # command (waits for player entry) or timer (async timer driven)
    server_tick_time = 5.0          # time between server ticks (in seconds) (usually 1.0 for 'timer' tick method)
    gametime_to_realtime = 1        # meaning: game time is X times the speed of real time (only used with "timer" tick method) (>=0)
    max_wait_hours = 2              # the max. number of hours (gametime) the player is allowed to wait (>=0)
    display_gametime = False        # enable/disable display of the game time at certain moments
    epoch = None                    # type: datetime.datetime # start date/time of the game clock
    startlocation_player = None     # type: str # name of the location where a player starts the game in
    startlocation_wizard = None     # type: str # name of the location where a wizard player starts the game in
    savegames_enabled = True        # allow savegames?
    show_exits_in_look = True       # with the look command, also show exit descriptions automatically?
    license_file = None             # type: str # game license file, if applicable
    mud_host = None                 # type: str # for mud mode: hostname to bind the server on
    mud_port = None                 # type: str # for mud mode: port number to bind the server on

    def init(self, driver) -> None:
        """
        Called by the game driver when it is done with its initial initialization.
        Usually this is the place to tell the driver to (pre)load zones via driver.load_zones
        """
        pass

    def init_player(self, player) -> None:
        """
        Called by the game driver when it has created the player object.
        You can set the hint texts on the player object, or change the state object, etc.
        For an IF game there is only one player. For a MUD game there will be many players,
        and every player that logs in can be further initialized here.
        """
        pass

    def welcome(self, player) -> Optional[str]:
        """
        Welcome text when player enters a new game
        If you return a string, it is used as an input prompt before continuing (a pause).
        """
        player.tell("<bright>Welcome to '%s'.</>" % self.name, end=True)
        player.tell("\n")
        return "Press enter to start."

    def welcome_savegame(self, player) -> Optional[str]:
        """
        Welcome text when player enters the game after loading a saved game
        If you return a string, it is used as an input prompt before continuing (a pause).
        """
        player.tell("<bright>Welcome back to '%s'.</>" % self.name, end=True)
        player.tell("\n")
        return "Press enter to continue where you were before."

    def goodbye(self, player) -> None:
        """goodbye text when player quits the game"""
        player.tell("Goodbye! We hope you enjoyed playing.")
        player.tell("\n")

    def completion(self, player) -> None:
        """congratulation text / finale when player finished the game (story_complete event)"""
        player.tell("<bright>Congratulations! You've finished the game!</>")

    def _verify(self, driver) -> None:
        """verify correctness and compatibility of the story configuration"""
        from tale import __version__ as tale_version_str
        tale_version = distutils.version.LooseVersion(tale_version_str)
        tale_version_required = distutils.version.LooseVersion(self.requires_tale)
        if tale_version < tale_version_required:
            raise StoryConfigError("This game requires tale " + self.requires_tale + ", but " + tale_version_str + " is installed.")

    def _get_config(self) -> "_Storyconfig":
        # create a copy of the story's configuration settings
        return _Storyconfig(self)


class _Storyconfig:   # XXX get rid of this
    def __init__(self, story: Storybase) -> None:
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
            "player_money",
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
            "show_exits_in_look",
            "license_file",
            "mud_host",
            "mud_port"
        }
        for attr in config_items:
            setattr(self, attr, getattr(story, attr))

    def __eq__(self, other: Any) -> bool:
        return self.__dict__ == other.__dict__
