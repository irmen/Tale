"""
Embedded Demo story, start it with python -m tale.demo.story

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import pathlib
import sys
from typing import Optional

import tale
from tale.driver import Driver
from tale.main import run_from_cmdline
from tale.player import Player
from tale.story import *


class Story(StoryBase):
    # create story configuration and customize:
    config = StoryConfig()
    config.name = "Tale demo story"
    config.author = "Irmen de Jong"
    config.author_address = "irmen@razorvine.net"
    config.version = tale.__version__
    config.supported_modes = {GameMode.IF, GameMode.MUD}
    config.player_name = "julie"
    config.player_gender = "f"
    config.player_race = "human"
    config.playable_races = {"human"}
    config.player_money = 15.5
    config.money_type = MoneyType.MODERN
    config.server_tick_method = TickMethod.TIMER
    config.server_tick_time = 0.5
    config.gametime_to_realtime = 5
    config.display_gametime = True
    config.startlocation_player = "house.livingroom"
    config.startlocation_wizard = "house.livingroom"
    config.zones = ["house"]

    def init(self, driver: Driver) -> None:
        pass

    def init_player(self, player: Player) -> None:
        player.money = 12.65

    def welcome(self, player: Player) -> Optional[str]:
        player.tell("<bright>Welcome to '%s'.</>" % self.config.name, end=True)
        player.tell("This is a tiny embedded story to check out a running Tale environment.")
        player.tell("Try to communicate with your pet, and exit the house to win the game.")
        player.tell("\n")
        player.tell("\n")
        return None

    def welcome_savegame(self, player: Player) -> Optional[str]:
        return None  # not supported in demo

    def goodbye(self, player: Player) -> None:
        player.tell("Thanks for trying out Tale!")


if __name__ == "__main__":
    # story is invoked as a script, start it in the Tale Driver.
    gamedir = pathlib.Path(__file__).parent
    if gamedir.is_dir() or gamedir.is_file():
        cmdline_args = sys.argv[1:]
        cmdline_args.insert(0, "--game")
        cmdline_args.insert(1, str(gamedir))
        run_from_cmdline(cmdline_args)
    else:
        print("Cannot load the story files from:", gamedir, file=sys.stderr)
        print("\nIt looks like you tried running the built-in demo story, "
              "but the tale library has been installed as an 'egg' or zip-file "
              "rather than normal files in your packages directory.\n"
              "This is not yet supported, sorry. "
              "Either re-install tale as normal files or just try any of the separate demo stories that come with it!\n",
              file=sys.stderr)
        raise SystemExit
