"""
Demo story.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import print_function, division, unicode_literals
import datetime
from tale import color

try:
    import colorama
except ImportError:
    print("\n(Note: Tale can use Colorama to add some effects to the console output.")
    print("You don't have it installed, so Tale will now use plain text output.)\n")


class Story(object):
    config = dict(
        name = "Tale Demo",
        author = "Irmen de Jong",
        author_address = "irmen@razorvine.net",
        version = "0.8",                 # arbitrary but is used to check savegames for compatibility
        requires_tale = "0.7",           # tale library required to run the game
        player_name = None,              # set a name to create a prebuilt player, None to use the character builder
        player_gender = None,            # m/f/n
        player_race = None,              # default is "human" ofcourse, but you can select something else if you want
        money_type = "modern",           # money type modern/fantasy
        server_tick_method = "timer",    # 'command' (waits for player entry) or 'timer' (async timer driven)
        server_tick_time = 1.0,          # time between server ticks (in seconds) (usually 1.0 for 'timer' tick method)
        gametime_to_realtime = 5,        # meaning: game time is X times the speed of real time (only used with "timer" tick method)
        display_gametime = True,         # enable/disable display of the game time at certain moments
        epoch = datetime.datetime(2012, 4, 19, 14, 0, 0),    # start date/time of the game clock
        startlocation_player = "town.square",
        startlocation_wizard = "wizardtower.hall",
        )

    resources = None    # will be set by driver init()
    driver = None       # will be set by driver init()

    def init(self, driver):
        """Called by the game driver when it is done with its initialization"""
        self.driver = driver
        self.resources = driver.game_resource

    def welcome(self, player):
        """welcome text when player enters a new game"""
        player.tell(color.bright("Welcome to %s." % self.config["name"]), end=True)
        player.tell("\n")
        player.tell(self.resources.load_text("messages/welcome.txt"))
        player.tell("\n")
        player.tell("\n")

    def welcome_savegame(self, player):
        """welcome text when player enters the game after loading a saved game"""
        player.tell(color.bright("Welcome back to %s." % self.config["name"]), end=True)
        player.tell("\n")
        player.tell(self.resources.load_text("messages/welcome.txt"))
        player.tell("\n")
        player.tell("\n")

    def goodbye(self, player):
        """goodbye text when player quits the game"""
        player.tell("Goodbye, %s. Please come back again soon." % player.title)
        player.tell("\n")

    def completion(self, player):
        """congratulation text / finale when player finished the game (story_complete event)"""
        player.tell(color.bright("Congratulations! You've finished the game!"))
