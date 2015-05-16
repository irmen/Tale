# coding=utf-8
"""
'Circle' -  an attempt to run the CircleMUD world data.

Written for Tale IF framework.
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
# @todo: this game is not yet finished and is excluded in the MANIFEST.in for now

from __future__ import absolute_import, print_function, division, unicode_literals
import sys
import datetime
from tale.driver import StoryConfig
from tale.main import run_story
from zones import init_zones


class Story(object):
    config = StoryConfig(
        name="Circle",
        author="Irmen de Jong",
        author_address="irmen@razorvine.net",
        version="1.1",                  # arbitrary but is used to check savegames for compatibility
        requires_tale="2.2",            # tale library required to run the game
        supported_modes={"mud"},        # what driver modes (if/mud) are supported by this story
        player_name=None,               # set a name to create a prebuilt player, None to use the character builder
        player_gender=None,             # m/f/n
        player_race=None,               # default is "human" ofcourse, but you can select something else if you want
        player_money=0.0,               # starting money
        money_type="fantasy",           # money type modern/fantasy/None
        server_tick_method="timer",     # 'command' (waits for player entry) or 'timer' (async timer driven)
        server_tick_time=1.0,           # time between server ticks (in seconds) (usually 1.0 for 'timer' tick method)
        gametime_to_realtime=5,         # meaning: game time is X times the speed of real time (only used with "timer" tick method) (>=0)
        max_wait_hours=2,               # the max. number of hours (gametime) the player is allowed to wait (>=0)
        display_gametime=True,          # enable/disable display of the game time at certain moments
        epoch=datetime.datetime(2015, 5, 14, 14, 0, 0),       # start date/time of the game clock
        startlocation_player="midgaard_city.temple",
        startlocation_wizard="god_simplex.boardroom",
        savegames_enabled=False,
        show_exits_in_look=False,       # circle room descriptions contain hints about the exits, no need to show this twice
        license_file=None,
        mud_host="localhost",
        mud_port=8200
    )

    driver = None     # will be set by driver init()

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
        player.tell("<bright>Hello, <player>%s</><bright>!  Welcome to '%s'.</>" % (player.title, self.config.name), end=True)
        player.tell("--", end=True)

    def welcome_savegame(self, player):
        pass    # not used in MUD

    def goodbye(self, player):
        """goodbye text when player quits the game"""
        player.tell("Goodbye. Please come back again soon to finish the story.")
        player.tell("\n")

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
