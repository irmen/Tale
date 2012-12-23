"""
'Zed is me' -  a Zombie survival adventure

Written for Tale IF framework.
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
# @todo: this game is not yet finished and is excluded in the MANIFEST.in for now

from __future__ import absolute_import, print_function, division, unicode_literals

if __name__=="__main__":
    # story is invoked as a script, start it in the Tale Driver.
    from tale.driver import Driver
    driver = Driver()
    driver.start(["-g", "."])
    raise SystemExit(0)


class Story(object):
    config = dict(
        name = "Zed is me",
        author = "Irmen de Jong",
        author_address = "irmen@razorvine.net",
        version = "0.4",                 # arbitrary but is used to check savegames for compatibility
        requires_tale = "0.8",           # tale library required to run the game
        player_name = "julie",           # set a name to create a prebuilt player, None to use the character builder
        player_gender = "f",             # m/f/n
        player_race = "human",           # default is "human" ofcourse, but you can select something else if you want
        money_type = "modern",           # money type modern/fantasy
        server_tick_method = "command",  # 'command' (waits for player entry) or 'timer' (async timer driven)
        server_tick_time = 5.0,          # time between server ticks (in seconds) (usually 1.0 for 'timer' tick method)
        gametime_to_realtime = 1,        # meaning: game time is X times the speed of real time (only used with "timer" tick method) (>=0)
        max_wait_hours = 2,              # the max. number of hours (gametime) the player is allowed to wait (>=0)
        display_gametime = False,        # enable/disable display of the game time at certain moments
        epoch = None,                    # start date/time of the game clock
        startlocation_player = "house.livingroom",
        startlocation_wizard = "house.livingroom",
        savegames_enabled = True
    )

    vfs = None        # will be set by driver init()
    driver = None     # will be set by driver init()

    def init(self, driver):
        """Called by the game driver when it is done with its initial initialization"""
        self.driver = driver
        self.vfs = driver.vfs

    def init_player(self, player):
        """
        Called by the game driver when it has created the player object.
        You can set the hint texts on the player object, or change the state object, etc.
        """
        pass

    def welcome(self, player):
        """welcome text when player enters a new game"""
        player.tell("<bright>Welcome to '%s'.</>" % self.config["name"], end=True)
        player.tell("\n")
        self.display_text_file(player, "messages/welcome.txt")
        player.tell("\n")
        player.input("\nPress enter to continue. ")
        player.tell("\n")

    def welcome_savegame(self, player):
        """welcome text when player enters the game after loading a saved game"""
        player.tell("<bright>Welcome back to '%s'.</>" % self.config["name"], end=True)
        player.tell("\n")
        self.display_text_file(player, "messages/welcome.txt")
        player.tell("\n")
        player.input("\nPress enter to continue where you were before. ")
        player.tell("\n")

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
        for paragraph in self.vfs.load_text(filename).split("\n\n"):
            if paragraph.startswith("\n"):
                player.tell("\n")
            player.tell(paragraph, end=True)
