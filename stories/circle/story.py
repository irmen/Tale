# coding=utf-8
"""
'Circle' -  an attempt to run the CircleMUD world data.

Written for Tale IF framework.
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import sys
import datetime
from tale.story import Storybase
from tale.main import run_story
from zones import init_zones


class Story(Storybase):
    name = "Circle"
    author = "Irmen de Jong"
    author_address = "irmen@razorvine.net"
    version = "1.1"
    requires_tale = "2.6"
    supported_modes = {"mud"}
    player_name = None
    player_gender = None
    player_race = None
    player_money = 0.0
    money_type = "fantasy"
    server_tick_method = "timer"
    server_tick_time = 1.0
    gametime_to_realtime = 5
    display_gametime = True
    epoch = datetime.datetime(2015, 5, 14, 14, 0, 0)       # start date/time of the game clock
    startlocation_player = "midgaard_city.temple"
    startlocation_wizard = "god_simplex.boardroom"
    savegames_enabled = False
    show_exits_in_look = False
    mud_host = "localhost"
    mud_port = 8200

    driver = None     # will be set by init()

    def init(self, driver):
        """Called by the game driver when it is done with its initial initialization"""
        self.driver = driver
        init_zones()

    def init_player(self, player):
        """
        Called by the game driver when it has created the player object.
        You can set the hint texts on the player object, or change the state object, etc.
        """
        pass

    def welcome(self, player):
        """
        Welcome text when player enters a new game
        If you return a string, it is used as an input prompt before continuing (a pause).
        """
        player.tell("<bright>Hello, <player>%s</><bright>!  Welcome to '%s'.</>" % (player.title, self.name), end=True)
        player.tell("--", end=True)

    def completion(self, player):
        """congratulation text / finale when player finished the game (story_complete event)"""
        # @TODO: determine fail/success
        self.display_text_file(player, "messages/completion_success.txt")
        # self.display_text_file(player, "messages/completion_failed.txt")

    def display_text_file(self, player, filename):
        text = self.driver.resources[filename].data
        for paragraph in text.split("\n\n"):
            if paragraph.startswith("\n"):
                player.tell("\n")
            player.tell(paragraph, end=True)


if __name__ == "__main__":
    # story is invoked as a script, start it in the Tale Driver.
    run_story(sys.path[0])
