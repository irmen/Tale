"""
Main startup class

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import sys
import argparse
import traceback
from typing import Dict, Any, Sequence
from . import __version__
from .tio import DEFAULT_SCREEN_DELAY
from .driver import Driver


def parse_cmdline(command_line_args: Sequence[str]) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="""
        Tale framework %s game driver. Use this to launch a game and specify some settings.
        Sometimes the game will provide its own startup script that invokes this automatically.
        If it doesn't, refer to the options to see how to launch it manually instead.
        """ % __version__)
    parser.add_argument('-g', '--game', type=str, help='path to the game directory', required=True)
    parser.add_argument('-d', '--delay', type=int, help='screen output delay for IF mode (milliseconds, 0=no delay)',
                        default=DEFAULT_SCREEN_DELAY)
    parser.add_argument('-m', '--mode', type=str, help='game mode, default=if', default="if", choices=["if", "mud"])
    parser.add_argument('-i', '--gui', help='gui interface', action='store_true')
    parser.add_argument('-w', '--web', help='web browser interface', action='store_true')
    parser.add_argument('-z', '--wizard', help='force wizard mode on if story character (for debug purposes)', action='store_true')
    return vars(parser.parse_args(command_line_args))


def run_from_cmdline(cmdline: Sequence[str]) -> None:
    kwargs = parse_cmdline(cmdline)
    try:
        Driver().start(**kwargs)
    except:
        if kwargs["gui"]:
            tb = traceback.format_exc()
            from .tio import tkinter_io
            tkinter_io.show_error_dialog("Exception during start", "An error occurred while starting up the game:\n\n" + tb)
        raise


if __name__ == "__main__":
    run_from_cmdline(sys.argv[1:])
