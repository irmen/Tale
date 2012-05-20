"""
'Zed is me' -  a Zombie survival adventure

Written for Tale IF framework.
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
# @todo: this game is not yet finished and is excluded in the MANIFEST.in for now


class Story(object):
    config = dict(
        name = "Zed is me",
        author = "Irmen de Jong",
        author_address = "irmen@razorvine.net",
        version = "0.2",                 # arbitrary but is used to check savegames for compatibility
        requires_tale = "0.5",           # tale library required to run the game
        player_name = "julie",           # set a name to create a prebuilt player, None to use the character builder
        player_gender = "f",             # m/f/n
        player_race = "human",           # default is "human" ofcourse, but you can select something else if you want
        max_score = 100,                 # arbitrary, but when max score is reached, the game is supposed to end. Use 0 or None to disable scoring.
        server_tick_method = "command",  # 'command' (waits for player entry) or 'timer' (async timer driven)
        server_tick_time = 5.0,          # time between server ticks (in seconds) (usually 1.0 for 'timer' tick method)
        gametime_to_realtime = 1,        # meaning: game time is X times the speed of real time (only used with "timer" tick method)
        display_gametime = False,        # enable/disable display of the game time at certain moments
        epoch = None,                    # start date/time of the game clock
        startlocation_player = "house.livingroom",
        startlocation_wizard = "house.livingroom",
    )

    resources = None    # will be set by driver init()
    driver = None       # will be set by driver init()

    def init(self, driver):
        """Called by the game driver when it is done with its initialization"""
        self.driver = driver
        self.resources = driver.game_resource

    def display_text_file(self, player, filename):
        for paragraph in self.resources.load_text(filename).split("\n\n"):
            if paragraph.startswith("\n"):
                player.tell("\n")
            player.tell(paragraph, end=True)

    def welcome(self, player):
        """welcome text when player enters a new game"""
        player.tell("Welcome to '%s'." % self.config["name"], end=True)
        player.tell("\n")
        self.display_text_file(player, "messages/welcome.txt")
        player.tell("\n")
        self.driver.input("\nPress enter to continue. ")
        player.tell("\n")

    def welcome_savegame(self, player):
        """welcome text when player enters the game after loading a saved game"""
        player.tell("Welcome back to '%s'." % self.config["name"], end=True)
        player.tell("\n")
        self.display_text_file(player, "messages/welcome.txt")
        player.tell("\n")
        self.driver.input("\nPress enter to continue where you were before. ")
        player.tell("\n")

    def goodbye(self, player):
        """goodbye text when player quits the game"""
        player.tell("Goodbye. Please come back again soon to finish the story.")
        player.tell("\n")

    def completion(self, player):
        """congratulation text / finale when player finished the game (story_complete event)"""
        if player.score >= self.config["max_score"]:
            self.display_text_file(player, "messages/completion_success.txt")
        else:
            self.display_text_file(player, "messages/completion_failed.txt")
