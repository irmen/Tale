"""
Console-based input/output.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import threading
import sys
from . import color

if sys.version_info < (3, 0):
    input = raw_input
else:
    input = input

__all__ = ["AsyncInput", "input", "input_line", "supports_delayed_output", "output", "break_pressed"]


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
        print()
        print(color.dim(">> "), end="")
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
    for line in lines:
        print(line)
    sys.stdout.flush()


def break_pressed(player):
    print(CTRL_C_MESSAGE)
    sys.stdout.flush()
