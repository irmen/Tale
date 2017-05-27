"""
Story configuration and base classes to create your own story with.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import datetime
import distutils.version
import enum
from typing import Optional, Any, List

from . import __version__ as tale_version_str
from .errors import StoryConfigError

__all__ = ["TickMethod", "GameMode", "MoneyType", "StoryBase", "StoryConfig"]


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


class StoryConfig:
    """
    Story configuration settings.
    The reason this is in a separate class, is that these settings are all simple values
    and are serializable, so they can be saved to disk as part of a save game file.
    """
    def __init__(self) -> None:
        self.name = None                     # type: str # the name of the story
        self.author = None                   # type: str # the story's author name
        self.author_address = None           # type: str # the author's email address
        self.version = "1.5"                 # arbitrary but is used to check savegames for compatibility
        self.requires_tale = "3.3"           # tale library required to run the game
        self.supported_modes = {GameMode.IF}    # what driver modes (if/mud) are supported by this story
        self.player_name = None              # type: str # set a name to create a prebuilt player, None to use the character builder
        self.player_gender = None            # type: str # m/f/n
        self.player_race = None              # type: str # default is "human" ofcourse, but you can select something else if you want
        self.player_money = 0.0              # starting money
        self.money_type = MoneyType.NOTHING  # money type modern/fantasy/nothing
        self.server_tick_method = TickMethod.COMMAND   # command (waits for player entry) or timer (async timer driven)
        self.server_tick_time = 5.0          # time between server ticks (in seconds) (usually 1.0 for 'timer' tick method)
        self.gametime_to_realtime = 1        # meaning: game time is X times real time (only used with "timer" tick method) (>=0)
        self.max_wait_hours = 2              # the max. number of hours (gametime) the player is allowed to wait (>=0)
        self.display_gametime = False        # enable/disable display of the game time at certain moments
        self.epoch = None                    # type: datetime.datetime # start date/time of the game clock
        self.startlocation_player = None     # type: str # name of the location where a player starts the game in
        self.startlocation_wizard = None     # type: str # name of the location where a wizard player starts the game in
        self.savegames_enabled = True        # allow savegames?
        self.show_exits_in_look = True       # with the look command, also show exit descriptions automatically?
        self.license_file = None             # type: str # game license file, if applicable
        self.mud_host = None                 # type: str # for mud mode: hostname to bind the server on
        self.mud_port = None                 # type: int # for mud mode: port number to bind the server on
        self.zones = []                      # type: List[str]  # names of zone modules to load, in this order
        self.server_mode = GameMode.IF       # the actual game mode the server is operating in (will be set at startup time)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, StoryConfig) and vars(self) == vars(other)


class StoryBase:
    """base class for tale story classes."""
    config = StoryConfig()

    def init(self, driver) -> None:
        """
        Called by the game driver when it is done with its initial initialization.
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
        player.tell("<bright>Welcome to '%s'.</>" % self.config.name, end=True)
        player.tell("\n")
        return "Press enter to start."

    def welcome_savegame(self, player) -> Optional[str]:
        """
        Welcome text when player enters the game after loading a saved game
        If you return a string, it is used as an input prompt before continuing (a pause).
        """
        player.tell("<bright>Welcome back to '%s'.</>" % self.config.name, end=True)
        player.tell("\n")
        return "Press enter to continue where you were before."

    def goodbye(self, player) -> None:
        """goodbye text when player quits the game"""
        player.tell("Goodbye! We hope you enjoyed playing.")
        player.tell("\n")

    def _verify(self, driver) -> None:
        """verify correctness and compatibility of the story configuration"""
        if not isinstance(self.config, StoryConfig):
            raise StoryConfigError("Story class must have config attribute of type StoryConfig, containing the story config settings")
        if not self.config.name:
            raise StoryConfigError("Story's config must specify story name, and other config items")
        if not (type(self.config.supported_modes) is set and all(type(m) is GameMode for m in self.config.supported_modes)):
            raise StoryConfigError("Story's config supported_modes is of invalid type")
        if type(self.config.money_type) is not MoneyType:
            raise StoryConfigError("Story's config money_type is of invalid type")
        if type(self.config.server_tick_method) is not TickMethod:
            raise StoryConfigError("Story's config server_tick_method is of invalid type")
        tale_version = distutils.version.LooseVersion(tale_version_str)
        tale_version_required = distutils.version.LooseVersion(self.config.requires_tale)
        if tale_version < tale_version_required:
            raise StoryConfigError("This game requires tale " + self.config.requires_tale + ", but " + tale_version_str + " is installed.")
