"""
Embedded Demo story, start it with python -m tale.demo.story

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import os
import sys
import tale
from tale.story import *
from tale.main import run_story


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
    config.player_money = 15.5
    config.money_type = MoneyType.MODERN
    config.server_tick_method = TickMethod.TIMER
    config.server_tick_time = 1.0
    config.gametime_to_realtime = 5
    config.display_gametime = True
    config.startlocation_player = "house.livingroom"
    config.startlocation_wizard = "house.livingroom"

    def init(self, driver):
        driver.load_zones(["house"])

    def init_player(self, player):
        player.money = 12.65

    def welcome(self, player):
        player.tell("<bright>Welcome to '%s'.</>" % self.config.name, end=True)
        player.tell("This is a tiny embedded story to check out a running Tale environment.")
        player.tell("Try to communicate with your pet, and exit the house to win the game.")
        player.tell("\n")
        player.tell("\n")

    def welcome_savegame(self, player):
        pass  # not supported in demo

    def goodbye(self, player):
        player.tell("Thanks for trying out Tale!")

    def completion(self, player):
        """congratulation text / finale when player finished the game (story_complete event)"""
        player.tell("Congratulations on escaping the house! Someone else has to look after Garfield now though...")


if __name__ == "__main__":
    # story is invoked as a script, start it in the Tale Driver.
    gamedir = os.path.dirname(__file__)
    gui = len(sys.argv) > 1 and sys.argv[1] == "--gui"
    web = len(sys.argv) > 1 and sys.argv[1] == "--web"
    mud = len(sys.argv) > 1 and sys.argv[1] == "--mud"
    run_story(gamedir, gui, web, mud)
