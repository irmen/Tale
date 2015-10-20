# coding=utf-8
"""
Story configuration and base classes to create your own story with.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals


class _Storyconfig(object):
    def __init__(self, story):
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
        for attr in config_items:
            setattr(self, attr, getattr(story, attr))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Storybase(object):
    """base class for tale story classes."""
    name = None                     # the name of the story
    author = None                   # the story's author name
    author_address = None           # the author's email address
    version = "1.1"                 # arbitrary but is used to check savegames for compatibility
    requires_tale = "2.6"           # tale library required to run the game
    supported_modes = {"if"}        # what driver modes (if/mud) are supported by this story
    player_name = None              # set a name to create a prebuilt player, None to use the character builder
    player_gender = None            # m/f/n
    player_race = None              # default is "human" ofcourse, but you can select something else if you want
    player_money = 0.0              # starting money
    money_type = None               # money type modern/fantasy/None
    server_tick_method = "command"  # 'command' (waits for player entry) or 'timer' (async timer driven)
    server_tick_time = 5.0          # time between server ticks (in seconds) (usually 1.0 for 'timer' tick method)
    gametime_to_realtime = 1        # meaning: game time is X times the speed of real time (only used with "timer" tick method) (>=0)
    max_wait_hours = 2              # the max. number of hours (gametime) the player is allowed to wait (>=0)
    display_gametime = False        # enable/disable display of the game time at certain moments
    epoch = None                    # start date/time of the game clock
    startlocation_player = None     # name of the location where a player starts the game in
    startlocation_wizard = None     # name of the location where a wizard player starts the game in
    savegames_enabled = True        # allow savegames?
    show_exits_in_look = True       # with the look command, also show exit descriptions automatically?
    license_file = None             # game license file, if applicable
    mud_host = None                 # for mud mode: hostname to bind the server on
    mud_port = None                 # for mud mode: port number to bind the server on

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

    def _get_config(self):
        # create a copy of the story's configuration settings
        return _Storyconfig(self)
