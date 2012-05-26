"""
Package containing new and overridden game commands.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from tale.cmds.decorators import wizcmd, cmd


def register_all(cmd_processor):
    pass
    # cmd_processor.add("demo", do_demo, "wizard")
    # cmd_processor.add("demo2", do_demo2)
    # cmd_processor.override("examine", do_examine)


@wizcmd
def do_demo(player, parsed, **ctx):
    player.tell("DEMO WIZARD COMMAND")

@cmd
def do_demo2(player, parsed, **ctx):
    player.tell("DEMO COMMAND")

@cmd
def do_examine(player, parsed, **ctx):
    player.tell("EXAMINE OVERRIDE")
