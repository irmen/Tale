import os
import sys

try:
    import tale.main
except ImportError:
    if os.path.exists("../../tale/__init__.py"):
        sys.path.insert(0, os.path.abspath("../.."))
        import tale.main
    else:
        import tkinter
        import tkinter.messagebox as tkmsgbox
        root = tkinter.Tk()
        root.withdraw()
        tkmsgbox.showerror("Installation error", "Cannot launch the game:\nTale is not properly installed.", master=root)
        raise SystemExit()

tale.main.run_from_cmdline(["--gui", "--game", "."])
