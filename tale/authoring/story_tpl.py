#! /usr/bin/env python3
"""
'{name}'
by {author} - {author_email}
"""

import sys
from tale.story import *


class Story(StoryBase):
    # Create your story configuration and customize it here.
    # Look at the options in StoryConfig to see what you can change.
    config = StoryConfig()
    config.name = "{name}"
    config.author = "{author}"
    config.author_address = "{author_email}"
    config.version = "1.0"
    config.requires_tale = "{tale_version}"
    config.supported_modes = {{{game_mode}}}
    config.money_type = {money_type}
    config.player_money = {money}
    config.player_name = "{player_name}"
    config.player_gender = "{player_gender}"
    config.startlocation_player = "house.livingroom"
    config.zones = ["house"]
    # Your story-specific configuration fields should be added below.
    # You can override various methods of the StoryBase class,
    # have a look at the Tale example stories to learn how you can use these.


if __name__ == "__main__":
    # story is invoked as a script, start it.
    from tale.main import run_from_cmdline
    run_from_cmdline(["--game", sys.path[0]])
