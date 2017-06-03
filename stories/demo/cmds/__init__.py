"""
Package containing new and overridden game commands.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from tale.player import Player
from tale.util import Context
from tale.cmds import wizcmd, cmd
from tale.base import ParseResult


@wizcmd("demo")
def do_demo(player: Player, parsed: ParseResult, ctx: Context) -> None:
    """demo wizard command"""
    player.tell("DEMO WIZARD COMMAND")


@cmd("demo2")
def do_demo2(player: Player, parsed: ParseResult, ctx: Context) -> None:
    """demo command"""
    player.tell("DEMO COMMAND")


@cmd("coin")
def do_coin(player: Player, parsed: ParseResult, ctx: Context) -> None:
    """coin command that overwrites the default version"""
    player.tell("COIN OVERRIDE")


@cmd("score")
def do_score(player: Player, parsed: ParseResult, ctx: Context) -> None:
    """Show your current score in the game."""
    player.tell("You have taken %d turns so far." % player.turns)
