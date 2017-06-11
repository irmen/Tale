"""
Demo story.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import datetime
import sys
from typing import Optional

from tale.driver import Driver
from tale.hints import Hint
from tale.player import Player
from tale.story import *


class Story(StoryBase):
    # create story configuration and customize:
    config = StoryConfig()
    config.name = "Tale Demo"
    config.author = "Irmen de Jong"
    config.author_address = "irmen@razorvine.net"
    config.version = "1.8"
    config.requires_tale = "3.4"
    config.supported_modes = {GameMode.IF, GameMode.MUD}
    config.player_money = 15.5
    config.playable_races = {"human", "elf", "dark-elf"}
    config.money_type = MoneyType.MODERN
    config.server_tick_method = TickMethod.TIMER
    config.server_tick_time = 1.0
    config.gametime_to_realtime = 5
    config.display_gametime = True
    config.epoch = datetime.datetime(2012, 4, 19, 14, 0, 0)
    config.startlocation_player = "town.square"
    config.startlocation_wizard = "wizardtower.hall"
    config.license_file = "messages/license.txt"
    config.zones = ["town", "wizardtower", "shoppe"]
    # story-specific fields follow:
    driver = None     # will be set by init()

    def init(self, driver: Driver) -> None:
        """Called by the game driver when it is done with its initial initialization."""
        self.driver = driver

    def init_player(self, player: Player) -> None:
        """
        Called by the game driver when it has created the player object.
        You can set the hint texts on the player object, or change the state object, etc.
        """
        player.hints.init([
            Hint(None, None, "Find a way to open the door that leads to the exit of the game."),
            Hint("unlocked_enddoor", None, "Step out through the door into the freedom!")
        ])

    def welcome(self, player: Player) -> Optional[str]:
        """welcome text when player enters a new game"""
        player.tell("<bright>Hello, <player>%s</><bright>! Welcome to %s.</>" % (player.title, self.config.name), end=True)
        player.tell("\n")
        player.tell(self.driver.resources["messages/welcome.txt"].text)
        player.tell("\n")
        return None

    def welcome_savegame(self, player: Player) -> Optional[str]:
        """welcome text when player enters the game after loading a saved game"""
        player.tell("<bright>Hello, <player>%s</><bright>, welcome back to %s.</>" % (player.title, self.config.name), end=True)
        player.tell("\n")
        player.tell(self.driver.resources["messages/welcome.txt"].text)
        player.tell("\n")
        return None

    def goodbye(self, player: Player) -> None:
        """goodbye text when player quits the game"""
        player.tell("Goodbye, %s. Please come back again soon." % player.title)
        player.tell("\n")


if __name__ == "__main__":
    # story is invoked as a script, start it.
    from tale.main import run_from_cmdline
    run_from_cmdline(["--game", sys.path[0]])
