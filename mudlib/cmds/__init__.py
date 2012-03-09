# package for all mud commands (non-soul)

from . import wizard
from . import normal


def register_all(cmd_processor):
    """
    Register all commands with the command processor.
    (Called from the game driver when it is starting up)
    """
    for command, func in wizard.all_commands.items():
        cmd_processor.add(command, func, "wizard")
    for command, func in normal.all_commands.items():
        cmd_processor.add(command, func, None)
