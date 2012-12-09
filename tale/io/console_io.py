"""
Console-based input/output.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import threading
import sys
from ..util import basestring_type
try:
    from . import colorama_patched as colorama
    colorama.init()
except ImportError:
    colorama = None

if sys.version_info < (3, 0):
    input = raw_input
else:
    input = input

__all__ = ["AsyncInput", "input", "input_line", "supports_delayed_output", "output", "break_pressed", "apply_style", "strip_text_styles"]


CTRL_C_MESSAGE = "\n* break: Use <quit> if you want to quit."


class AsyncInput(threading.Thread):
    def __init__(self, player):
        super(AsyncInput, self).__init__()
        self.player = player
        self.setDaemon(True)
        self.enabled = threading.Event()
        self.enabled.clear()
        self.start()
        self._stoploop = False

    def run(self):
        loop = True
        while loop:
            self.enabled.wait()
            if self._stoploop:
                break
            loop = input_line(self.player)
            self.enabled.clear()

    def enable(self):
        self.enabled.set()

    def disable(self):
        self.enabled.clear()

    def stop(self):
        self._stoploop = True
        self.enabled.set()
        self.join()


def input_line(player):
    """
    Input a single line of text by the player.
    Returns True if the input loop should continue as usual.
    Returns False if the input loop should be terminated (this could
    be the case when the player types 'quit', for instance).
    """
    try:
        print(apply_style("\n{dim}>>{/} "), end="")
        cmd = input().lstrip()
        player.input_line(cmd)
        if cmd == "quit":
            return False
    except KeyboardInterrupt:
        player.tell(CTRL_C_MESSAGE)
    except EOFError:
        pass
    return True


supports_delayed_output = True


def output(*lines):
    """Write some text to the visible output buffer."""
    for line in apply_style(lines=lines):
        print(line)
    sys.stdout.flush()


def break_pressed(player):
    print(apply_style(CTRL_C_MESSAGE))
    sys.stdout.flush()


if colorama is not None:
    style_colors = {
        "dim": colorama.Style.DIM,
        "normal": colorama.Style.NORMAL,
        "bright": colorama.Style.BRIGHT,
        "ul": colorama.Style.UNDERLINED,
        "rev": colorama.Style.REVERSEVID,
        "/": colorama.Style.RESET_ALL,
        "italic": colorama.Style.ITALIC,
        "blink": colorama.Style.BLINK,
        "black": colorama.Fore.BLACK,
        "red": colorama.Fore.RED,
        "green": colorama.Fore.GREEN,
        "yellow": colorama.Fore.YELLOW,
        "blue": colorama.Fore.BLUE,
        "magenta": colorama.Fore.MAGENTA,
        "cyan": colorama.Fore.CYAN,
        "white": colorama.Fore.WHITE,
        "bg:black": colorama.Back.BLACK,
        "bg:red": colorama.Back.RED,
        "bg:green": colorama.Back.GREEN,
        "bg:yellow": colorama.Back.YELLOW,
        "bg:blue": colorama.Back.BLUE,
        "bg:magenta": colorama.Back.MAGENTA,
        "bg:cyan": colorama.Back.CYAN,
        "bg:white": colorama.Back.WHITE,
        "living": colorama.Style.BRIGHT,
        "player": colorama.Style.BRIGHT,
        "item": colorama.Style.BRIGHT,
        "exit": colorama.Style.BRIGHT
    }
else:
    style_colors = None

def apply(line):
    if "{" not in line:
        return line
    if style_colors:
        for tag in style_colors:
            line = line.replace("{%s}" % tag, style_colors[tag])
    return line


def apply_style(line=None, lines=[]):
    """Convert style tags to colorama escape sequences suited for console text output"""
    if line is not None:
        return apply(line)
    return (apply(line) for line in lines)


def strip_text_styles(text):
    """remove any special text styling tags from the text (you can pass a single string, and also a list of strings)"""
    def strip(text):
        if "{" not in text:
            return text
        for tag in ("dim", "normal", "bright", "ul", "rev", "italic", "blink", "/",
                    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
                    "bg:black", "bg:red", "bg:green", "bg:yellow", "bg:blue", "bg:magenta", "bg:cyan", "bg:white",
                    "living", "player", "item", "exit"):
            text = text.replace("{%s}" % tag, "")
        return text
    if isinstance(text, basestring_type):
        return strip(text)
    return [strip(line) for line in text]
