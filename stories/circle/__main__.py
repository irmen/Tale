"""
This __main__.py file is used to make it very easy to launch stories as a zip file.
If you zip up the story's directory as "story.zip", you can then simply:

    $ python story.zip

to launch the game. (as long as you have Tale installed)
"""
import os
import sys
try:
    import tale.main
except ImportError as x:
    print("Error loading Tale: ", x, file=sys.stderr)
    print("To run this game you have to install the Tale library.\nUsually 'pip install tale' should be enough.\n", file=sys.stderr)
    input("Enter to exit: ")
    raise SystemExit


# insert path to this game and any necessary command line options (edit these if needed)
gamelocation = sys.path[0] or os.path.dirname(__file__)
args = ["--game", gamelocation, "--mode", "mud"] + sys.argv[1:]

# start the game
tale.main.run_from_cmdline(args)
