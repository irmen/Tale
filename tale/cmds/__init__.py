"""
Package for all mud commands (non-soul)

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals


abbreviations = {
    "n": "north",
    "e": "east",
    "s": "south",
    "w": "west",
    "ne": "northeast",
    "nw": "northwest",
    "se": "southeast",
    "sw": "southwest",
    "u": "up",
    "d": "down",
    "?": "help",
    "i": "inventory",
    "l": "look",
    "x": "examine",
    "exa": "examine",
    "inv": "inventory",
    "'": "say"
}


def register_all(cmd_processor):
    """
    Register all commands with the command processor.
    (Called from the game driver when it is starting up)
    """
    from . import wizard
    from . import normal
    normal.abbreviations = abbreviations    # used in help, look, examine
    for command, func in wizard.all_commands.items():
        cmd_processor.add(command, func, "wizard")
    for command, func in normal.all_commands.items():
        cmd_processor.add(command, func, None)
