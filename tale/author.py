"""
Utilities for story authors

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import zipfile
import sys
import os
from typing import Sequence
import tale
import tale.story
import tale.errors


main_py_template = """
\"\"\"
This __main__.py file is used to make it very easy to launch stories as a zip file.
If you zip up the story's directory as "story.zip", you can then simply:

    $ python story.zip

to launch the game. (as long as you have Tale installed)
\"\"\"
from __future__ import print_function
import os
import sys

if sys.version_info < (3, 5):
    raise SystemExit("You have to use Python 3.5 or newer to run this. (current version: %s %s)" %
                     (sys.executable, ".".join(str(v) for v in sys.version_info[:3])))

tale_error = None
try:
    import tale
    tale._check_required_libraries()
    import tale.main
    from distutils.version import LooseVersion
    if LooseVersion(tale.__version__) < LooseVersion("{required_tale_version}"):
        print("Tale version installed:", tale.__version__, file=sys.stderr)
        print("Tale version required : {required_tale_version}", file=sys.stderr) 
        tale_error = "installed Tale library version too old"
except ImportError as x:
    tale_error = str(x)
    
if tale_error:
    print("Error loading Tale: ", tale_error, file=sys.stderr)
    print("To run this game you have to install a recent enough Tale library.\\nRunning the command 'pip install --upgrade tale' usually fixes this.\\n", file=sys.stderr)
    print("Enter to exit: ", file=sys.stderr)
    input()
    raise SystemExit


# insert path to this game and any necessary command line options (edit these if needed)
gamelocation = sys.path[0] or os.path.dirname(__file__)
args = ["--game", gamelocation, "--mode", "{gamemode}"] + sys.argv[1:]

# start the game
tale.main.run_from_cmdline(args)

"""


def do_zip(path: str, zipfilename: str, embed_tale: bool=False, verbose: bool=False) -> None:
    """Zip a story (possibly including the tale library itself - but not its dependencies, to avoid license hassles) into a zip file."""
    if os.path.exists(zipfilename):
        raise IOError("output file already exists: " + zipfilename)
    with zipfile.ZipFile(zipfilename, mode="w", compression=zipfile.ZIP_DEFLATED) as zip:
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
            zip.writestr("__main__.py", main_py_template.format(gamemode=mode.value, required_tale_version=story.Story.config.requires_tale))
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
    if verbose:
        print("\nDone. Try running 'python {}'".format(zipfilename))


def run_from_cmdline(args: Sequence[str]) -> None:
    """Entrypoint from the commandline to invoke the available tools from this module."""
    if len(args) < 1:
        print("Give command to execute, one of:  zip")
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
    else:
        print("invalid command")
        raise SystemExit(1)


if __name__ == "__main__":
    run_from_cmdline(sys.argv[1:])
