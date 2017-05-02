import sys
import os

try:
    import tale.driver
    tale_from_lib = True
except ImportError:
    tale_from_lib = False

if not tale_from_lib:
    if os.path.exists("../../tale/__init__.py"):
        sys.path.insert(0, os.path.abspath("../.."))
        import tale.driver
    else:
        import tkinter
        import tkinter.messagebox as tkmsgbox
        root = tkinter.Tk()
        root.withdraw()
        tkmsgbox.showerror("Installation error", "Cannot launch the game:\nTale is not properly installed.", master=root)
        raise SystemExit()

tale.driver.Driver().start(game=".", gui=True)
