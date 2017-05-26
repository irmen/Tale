"""
Package for all mud commands (non-soul)

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from typing import Any, Dict, Callable, Tuple


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


# these will be filled by the @cmd and @wizcmd decorators when used
_all_commands = {}   # type: Dict[str, Callable]
_all_wizard_commands = {}   # type: Dict[str, Callable]
cmds_aliases = {}   # type: Dict[str, Tuple[str, ...]]  # commands -> tuple of one or more aliases


def register_all(cmd_processor: Any) -> None:
    """
    Register all commands with the command processor.
    (Called from the game driver when it is starting up)
    Note that we are relying on the command function to add itself (via the @cmd decorator)
    to the collection above. This way you can define commands anywhere without this
    code having to know that modules to scan. This is required for user story packages!
    """
    from . import wizard
    from . import normal
    for command, func in _all_wizard_commands.items():
        cmd_processor.add(command, func, "wizard")
    for command, func in _all_commands.items():
        cmd_processor.add(command, func, None)
