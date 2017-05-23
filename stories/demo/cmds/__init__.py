"""
Package containing new and overridden game commands.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from tale import util
from tale.cmds.decorators import wizcmd, cmd
from tale.driver import Commands
from tale.parseresult import ParseResult
from tale.player import Player


def register_all(cmd_processor: Commands) -> None:
    cmd_processor.add("demo", do_demo, "wizard")
    cmd_processor.add("demo2", do_demo2)
    cmd_processor.add("score", do_score)
    cmd_processor.override("coin", do_coin)


@wizcmd
def do_demo(player: Player, parsed: ParseResult, ctx: util.Context) -> None:
    """demo wizard command"""
    player.tell("DEMO WIZARD COMMAND")


@cmd
def do_demo2(player: Player, parsed: ParseResult, ctx: util.Context) -> None:
    """demo command"""
    player.tell("DEMO COMMAND")


@cmd
def do_coin(player: Player, parsed: ParseResult, ctx: util.Context) -> None:
    """coin override"""
    player.tell("COIN OVERRIDE")


@cmd
def do_score(player: Player, parsed: ParseResult, ctx: util.Context) -> None:
    """Show your current score in the game."""
    player.tell("You have taken %d turns so far." % player.turns)
