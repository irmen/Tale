# coding=utf-8
"""
Story configuration and base classes to create your own story with.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals


class Storybase(object):
    """base class for tale story classes."""

    def init(self, driver):
        """
        Called by the game driver when it is done with its initial initialization.
        Usually this is the place to tell the driver to (pre)load zones via driver.load_zones
        """
        pass

    def init_player(self, player):
        """
        Called by the game driver when it has created the player object.
        You can set the hint texts on the player object, or change the state object, etc.
        For an IF game there is only one player. For a MUD game there will be many players,
        and every player that logs in can be further initialized here.
        """
        pass

    def welcome(self, player):
        """
        Welcome text when player enters a new game
        If you return a string, it is used as an input prompt before continuing (a pause).
        """
        player.tell("<bright>Welcome to '%s'.</>" % self.config.name, end=True)
        player.tell("\n")
        return "Press enter to start."

    def welcome_savegame(self, player):
        """
        Welcome text when player enters the game after loading a saved game
        If you return a string, it is used as an input prompt before continuing (a pause).
        """
        player.tell("<bright>Welcome back to '%s'.</>" % self.config.name, end=True)
        player.tell("\n")
        return "Press enter to continue where you were before."

    def goodbye(self, player):
        """goodbye text when player quits the game"""
        player.tell("Goodbye! We hope you enjoyed playing.")
        player.tell("\n")

    def completion(self, player):
        """congratulation text / finale when player finished the game (story_complete event)"""
        player.tell("<bright>Congratulations! You've finished the game!</>")


class StoryConfig(object):
    """Container for the configuration settings for a Story"""
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

    def __init__(self, **kwargs):
        difference = self.config_items ^ set(kwargs)
        if difference:
            raise ValueError("invalid story config; mismatch in config arguments: "+str(difference))
        for k, v in kwargs.items():
            if k in self.config_items:
                setattr(self, k, v)
            else:
                raise AttributeError("unrecognised config attribute: " + k)

    def __eq__(self, other):
        return vars(self) == vars(other)

    @staticmethod
    def copy_from(config):
        assert isinstance(config, StoryConfig)
        return StoryConfig(**vars(config))
