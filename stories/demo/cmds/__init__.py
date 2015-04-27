# coding=utf-8
"""
Package containing new and overridden game commands.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from tale.cmds.decorators import wizcmd, cmd


def register_all(cmd_processor):
    cmd_processor.add("demo", do_demo, "wizard")
    cmd_processor.add("demo2", do_demo2)
    cmd_processor.add("score", do_score)
    cmd_processor.override("coin", do_coin)


@wizcmd
def do_demo(player, parsed, ctx):
    player.tell("DEMO WIZARD COMMAND")


@cmd
def do_demo2(player, parsed, ctx):
    player.tell("DEMO COMMAND")


@cmd
def do_coin(player, parsed, ctx):
    player.tell("COIN OVERRIDE")


@cmd
def do_score(player, parsed, ctx):
    """Show your current score in the game."""
    player.tell("You have taken %d turns so far." % player.turns)
