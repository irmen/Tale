"""
'Zed is me' -  a Zombie survival adventure

Written for Tale IF framework.
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import sys
from typing import Optional
from tale.story import *
from tale.player import Player
from tale.driver import Driver


class Story(StoryBase):
    # create story configuration and customize:
    config = StoryConfig()
    config.name = "Zed is me"
    config.author = "Irmen de Jong"
    config.author_address = "irmen@razorvine.net"
    config.version = "1.3"
    config.requires_tale = "3.0"
    config.supported_modes = {GameMode.IF}
    config.player_name = "julie"
    config.player_gender = "f"
    config.player_race = "human"
    config.startlocation_player = "houses.livingroom"
    config.startlocation_wizard = "houses.livingroom"
    config.zones = ["houses", "magnolia_st", "rose_st"]
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
        pass

    def welcome(self, player: Player) -> Optional[str]:
        """
        Welcome text when player enters a new game
        If you return a string, it is used as an input prompt before continuing (a pause).
        """
        player.tell("<bright>Welcome to '%s'.</>" % self.config.name, end=True)
        player.tell("\n")
        self.display_text_file(player, "messages/welcome.txt")
        player.tell("\n")
        return "Press enter to continue."

    def welcome_savegame(self, player: Player) -> Optional[str]:
        """
        Welcome text when player enters the game after loading a saved game
        If you return a string, it is used as an input prompt before continuing (a pause).
        """
        player.tell("<bright>Welcome back to '%s'.</>" % self.config.name, end=True)
        player.tell("\n")
        self.display_text_file(player, "messages/welcome.txt")
        player.tell("\n")
        return "Press enter to continue where you were before."

    def completion(self, player: Player) -> None:
        """congratulation text / finale when player finished the game (story_complete event)"""
        # @TODO: determine fail/success
        self.display_text_file(player, "messages/completion_success.txt")
        # self.display_text_file(player, "messages/completion_failed.txt")

    def display_text_file(self, player: Player, filename: str) -> None:
        text = self.driver.resources[filename].data
        for paragraph in text.split("\n\n"):
            if paragraph.startswith("\n"):
                player.tell("\n")
            player.tell(paragraph, end=True)


if __name__ == "__main__":
    # story is invoked as a script, start it in the Tale Driver.
    Driver().start(game=sys.path[0])
