# coding=utf-8
"""
Demo story.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import datetime
import sys
from tale.hints import Hint
from tale.story import Storybase
from tale.main import run_story


class Story(Storybase):
    name = "Tale Demo"
    author = "Irmen de Jong"
    author_address  ="irmen@razorvine.net"
    version = "1.3"
    requires_tale = "2.6"
    supported_modes = {"if", "mud"}
    player_money = 15.5
    money_type = "modern"
    server_tick_method = "timer"
    server_tick_time = 1.0
    gametime_to_realtime = 5
    display_gametime = True
    epoch = datetime.datetime(2012, 4, 19, 14, 0, 0)
    startlocation_player = "town.square"
    startlocation_wizard = "wizardtower.hall"
    license_file = "messages/license.txt"

    driver = None     # will be set by init()

    def init(self, driver):
        """Called by the game driver when it is done with its initial initialization"""
        self.driver = driver
        self.driver.load_zones(["town", "wizardtower", "shoppe"])

    def init_player(self, player):
        """
        Called by the game driver when it has created the player object.
        You can set the hint texts on the player object, or change the state object, etc.
        """
        player.hints.init([
            Hint(None, None, "Find a way to open the door that leads to the exit of the game."),
            Hint("unlocked_enddoor", None, "Step out through the door into the freedom!")
        ])

    def welcome(self, player):
        """welcome text when player enters a new game"""
        player.tell("<bright>Hello, <player>%s</><bright>! Welcome to %s.</>" % (player.title, self.name), end=True)
        player.tell("\n")
        player.tell(self.driver.resources["messages/welcome.txt"].data)
        player.tell("\n")

    def welcome_savegame(self, player):
        """welcome text when player enters the game after loading a saved game"""
        player.tell("<bright>Hello, <player>%s</><bright>, welcome back to %s.</>" % (player.title, self.name), end=True)
        player.tell("\n")
        player.tell(self.driver.resources["messages/welcome.txt"].data)
        player.tell("\n")

    def goodbye(self, player):
        """goodbye text when player quits the game"""
        player.tell("Goodbye, %s. Please come back again soon." % player.title)
        player.tell("\n")

    def completion(self, player):
        """congratulation text / finale when player finished the game (story_complete event)"""
        player.tell("<bright>Congratulations! You've finished the game!</>")


if __name__ == "__main__":
    # story is invoked as a script, start it in the Tale Driver.
    run_story(sys.path[0])
