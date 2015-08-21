# coding=utf-8
"""
'Zed is me' -  a Zombie survival adventure

Written for Tale IF framework.
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import sys
from tale.story import Storybase
from tale.main import run_story


class Story(Storybase):
    name = "Zed is me"
    author = "Irmen de Jong"
    author_address = "irmen@razorvine.net"
    version = "1.2"
    supported_modes = {"if"}
    player_name = "julie"
    player_gender = "f"
    player_race = "human"
    startlocation_player = "houses.livingroom"
    startlocation_wizard = "houses.livingroom"
    driver = None     # will be set by init()

    def init(self, driver):
        """Called by the game driver when it is done with its initial initialization"""
        self.driver = driver
        self.driver.load_zones(["houses", "magnolia_st", "rose_st"])

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
        player.tell("<bright>Welcome to '%s'.</>" % self.name, end=True)
        player.tell("\n")
        self.display_text_file(player, "messages/welcome.txt")
        player.tell("\n")
        return "Press enter to continue."

    def welcome_savegame(self, player):
        """
        Welcome text when player enters the game after loading a saved game
        If you return a string, it is used as an input prompt before continuing (a pause).
        """
        player.tell("<bright>Welcome back to '%s'.</>" % self.name, end=True)
        player.tell("\n")
        self.display_text_file(player, "messages/welcome.txt")
        player.tell("\n")
        return "Press enter to continue where you were before."

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
