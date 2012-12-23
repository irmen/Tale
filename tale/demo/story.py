"""
Embedded Demo story, start it with python -m tale.demo.story

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import os
import sys
import tale
import tale.vfs

if __name__=="__main__":
    # story is invoked as a script, start it in the Tale Driver.
    from tale.driver import Driver
    driver = Driver()
    with tale.vfs.vfs.open_read("demo/__init__.py") as x:
        gamedir = os.path.dirname(x.name)
    args = ["-g", gamedir, "--mode", "if"]
    if len(sys.argv) > 1 and sys.argv[1]=="--gui":
        args.append("--gui")
    driver.start(args)
    raise SystemExit(0)


class Story(object):
    config = dict(
        name = "Tale demo story",
        author = "Irmen de Jong",
        author_address = "irmen@razorvine.net",
        version = tale.__version__,      # arbitrary but is used to check savegames for compatibility
        requires_tale = tale.__version__, # tale library required to run the game
        player_name = "julie",           # set a name to create a prebuilt player, None to use the character builder
        player_gender = "f",             # m/f/n
        player_race = "human",           # default is "human" ofcourse, but you can select something else if you want
        money_type = "modern",           # money type modern/fantasy
        server_tick_method = "timer",    # 'command' (waits for player entry) or 'timer' (async timer driven)
        server_tick_time = 1.0,          # time between server ticks (in seconds) (usually 1.0 for 'timer' tick method)
        gametime_to_realtime = 5,        # meaning: game time is X times the speed of real time (only used with "timer" tick method) (>=0)
        max_wait_hours = 2,              # the max. number of hours (gametime) the player is allowed to wait (>=0)
        display_gametime = True,         # enable/disable display of the game time at certain moments
        epoch = None,                    # start date/time of the game clock
        startlocation_player = "house.livingroom",
        startlocation_wizard = "house.livingroom",
        savegames_enabled = False
    )

    vfs = None        # will be set by driver init()
    driver = None     # will be set by driver init()

    def init(self, driver):
        self.driver = driver
        self.vfs = driver.vfs

    def init_player(self, player):
        player.money = 12.65

    def welcome(self, player):
        player.tell("<bright>Welcome to '%s'.</>" % self.config["name"], end=True)
        player.tell("\n")

    def welcome_savegame(self, player):
        pass  # not supported in demo

    def goodbye(self, player):
        pass

    def completion(self, player):
        """congratulation text / finale when player finished the game (story_complete event)"""
        player.tell("Congratulations on finding the exit!")
