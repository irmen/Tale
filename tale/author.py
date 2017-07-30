"""
Utilities for story authors

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import zipfile
import zipapp
import sys
import os
from typing import Sequence
import tale
import tale.story
import tale.errors
import tale.vfs

vfs = tale.vfs.VirtualFileSystem(root_package="tale")


def do_zip(path: str, zipfilename: str, embed_tale: bool=False, verbose: bool=False) -> None:
    """Zip a story (possibly including the tale library itself - but not its dependencies, to avoid license hassles) into a zip file."""
    if os.path.exists(zipfilename):
        raise IOError("output file already exists: " + zipfilename)
    with zipfile.ZipFile(zipfilename + ".tmp", mode="w", compression=zipfile.ZIP_DEFLATED) as zip:
        prev_dir = os.getcwd()
        os.chdir(path)
        print("\nCreating zip file from '{}'...".format(path))
        has_main_py = False
        for base, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".")]
            files[:] = [f for f in files if not f.endswith(".pyc") and not f.endswith(".pyo")]
            for f in files:
                filename = os.path.join(base, f)
                has_main_py = has_main_py or (base in ('', '.') and f == "__main__.py")
                zip.write(filename)
                if verbose:
                    print(filename)
        if has_main_py:
            if verbose:
                print("\nThe story provided a __main__.py itself.")
                print("(we use this to be able to do 'python story.zip')")
        else:
            print("\nThe story didn't provide a __main__.py itself - creating one for you.")
            print("(needed to be able to do 'python story.zip')")
            import story
            possible_game_modes = story.Story.config.supported_modes
            if len(possible_game_modes) > 1:
                print("\nSupported game modes for this story:", ",".join([m.value for m in possible_game_modes]))
                while True:
                    try:
                        mode = tale.story.GameMode(input("Which mode do you want to use? "))
                        break
                    except ValueError:
                        pass
            else:
                # only one possible game mode, autoselect this one
                mode = possible_game_modes.pop()
            main_tpl = vfs["authoring/main_tpl.py"].text
            zip.writestr("__main__.py", main_tpl.format(gamemode=mode.value,
                                                        required_tale_version=story.Story.config.requires_tale))
        if embed_tale:
            os.chdir(os.path.dirname(tale.__file__))
            if verbose:
                print("\nEmbedding Tale library in zipfile... (source location: {})".format(os.getcwd()))
            for base, dirs, files in os.walk("."):
                dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".")]
                files[:] = [f for f in files if not f.endswith(".pyc") and not f.endswith(".pyo")]
                for f in files:
                    filename = os.path.join(base, f)
                    arcname = os.path.normpath(os.path.join("tale", filename))
                    zip.write(filename, arcname=arcname)
                    if verbose:
                        print(arcname)
        os.chdir(prev_dir)
    # use zipapp to add a posix shebang.
    # note: we can't use zipapp conveniently to create the whole zipfile because it also includes temp files that I don't want...
    zipapp.create_archive(zipfilename + ".tmp", zipfilename, interpreter="/usr/bin/env python3")
    os.remove(zipfilename + ".tmp")
    if verbose:
        print("\nDone. Try running 'python {}'".format(zipfilename))


def do_init(path: str) -> None:
    os.makedirs(path, exist_ok=True)
    if os.path.exists(os.path.join(path, "story.py")):
        raise SystemExit("output folder already contains a story.py file")
    print("------ Setting up new Tale story -----")
    name = input("Story name: ").strip()
    author = input("Story author name: ").strip()
    author_email = input("Story author email: ").strip()
    player_name = input("Player name: ").strip()
    player_gender = input("Player gender (m/f/n): ").strip()[:1]
    money_type = input("Money type (modern/fantasy/nothing): ").strip()
    if money_type != "nothing":
        money = float(input("Player start money amount: "))
    else:
        money = 0.0
    if money_type == "modern":
        money_type = "MoneyType.MODERN"
    elif money_type == "fantasy":
        money_type = "MoneyType.FANTASY"
    else:
        money_type = "MoneyType.NOTHING"
    game_mode = input("Game mode (if/mud): ").strip()
    if game_mode == "if":
        tick = input("Tick method (command/timer): ").strip()
        if tick == "command":
            tick = "TickMethod.COMMAND"
        else:
            tick = "TickMethod.TIMER"
        game_mode = "GameMode.IF"
    else:
        tick = "TickMethod.TIMER"
        game_mode = "GameMode.MUD"
    story_tpl = vfs["authoring/story_tpl.py"].text
    tale_version = tale.__version__
    with open(os.path.join(path, "story.py"), "wt") as out:
        out.write(story_tpl.format(**locals()))
    os.chmod(os.path.join(path, "story.py"), 0o755)
    os.mkdir(os.path.join(path, "zones"))
    with open(os.path.join(path, "zones/__init__.py"), "wt") as out:
        print("# Story zone modules go in this package", file=out)
        print("# See Tale example stories for more example code to learn.", file=out)
    house_tpl = vfs["authoring/house_tpl.py"].text
    with open(os.path.join(path, "zones/house.py"), "wt") as out:
        out.write(house_tpl)
    os.mkdir(os.path.join(path, "cmds"))
    with open(os.path.join(path, "cmds/__init__.py"), "wt") as out:
        print("# Custom commands should be defined in this file.", file=out)
        print("# see Tale example stories to learn how to do this.", file=out)
    os.mkdir(os.path.join(path, "messages"))
    with open(os.path.join(path, "messages/_readme.txt"), "wt") as out:
        print("Custom story message texts go in this folder.", file=out)
        print("See Tale example stories to learn how to do this.", file=out)
    print("\nDone. Go to the '{path}' directory and run story.py to play your game.".format(path=path))
    print("You can use the 'zip' command of this authoring tool to create a single\n"
          "zipfile from your story directory, for easy distribution later.")


def run_from_cmdline(args: Sequence[str]) -> None:
    """Entrypoint from the commandline to invoke the available tools from this module."""
    if len(args) < 1:
        print("Give command to execute, one of:  zip / init")
        raise SystemExit()
    if args[0] == "zip":
        args = args[1:]
        if len(args) < 2:
            print("Arguments for zip command are: [story-directory] [output-zip-file]  [-t] [-v]")
            print("   -t to embed the Tale library in the zipfile")
            print("   -v to enable verbose mode")
            raise SystemExit(1)
        verbose = "-v" in args
        embed_tale = "-t" in args
        do_zip(args[0], args[1], embed_tale, verbose)
    elif args[0] == "init":
        args = args[1:]
        if len(args) != 1:
            print("Arguments for init command are: [story-directory]")
            raise SystemExit(1)
        do_init(args[0])
    else:
        print("invalid command")
        raise SystemExit(1)


if __name__ == "__main__":
    run_from_cmdline(sys.argv[1:])
