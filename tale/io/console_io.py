"""
Console-based input/output.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import threading
import sys
import time
from . import styleaware_wrapper, iobase
try:
    from . import colorama_patched as colorama
    colorama.init()
except ImportError:
    colorama = None

if sys.version_info < (3, 0):
    input = raw_input
else:
    input = input

__all__ = ["ConsoleIo"]


if colorama is not None:
    style_colors = {
        "dim": colorama.Style.DIM,
        "normal": colorama.Style.NORMAL,
        "bright": colorama.Style.BRIGHT,
        "ul": colorama.Style.UNDERLINED,
        "rev": colorama.Style.REVERSEVID,
        "/": colorama.Style.RESET_ALL,
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
        "exit": colorama.Style.BRIGHT,
        "location": colorama.Style.BRIGHT
    }
    assert len(set(style_colors.keys()) ^ iobase.ALL_COLOR_TAGS) == 0, "mismatch in list of style tags"
else:
    style_colors = None


class AsyncConsoleInput(threading.Thread):
    def __init__(self, player):
        super(AsyncConsoleInput, self).__init__()
        self.player = player
        self.daemon = True
        self.enabled = threading.Event()
        self.enabled.clear()
        self._stoploop = False
        self.start()

    def run(self):
        loop = True
        while loop:
            self.enabled.wait()
            if self._stoploop:
                break
            loop = self.player.io.input_line(self.player)
            self.enabled.clear()

    def enable(self):
        self.enabled.set()

    def disable(self):
        self.enabled.clear()

    def stop(self):
        self._stoploop = True
        self.enabled.set()
        self.join()


class ConsoleIo(object):
    CTRL_C_MESSAGE = "\n* break: Use <quit> if you want to quit."

    def __init__(self):
        self.output_line_delay = 50   # milliseconds. (set to 0 to disable or to signify: doesn't support this)
        self.do_styles = True

    def get_async_input(self, player):
        return AsyncConsoleInput(player)

    def input(self, prompt=None):
        return input(prompt)

    def input_line(self, player):
        """
        Input a single line of text by the player.
        Returns True if the input loop should continue as usual.
        Returns False if the input loop should be terminated (this could
        be the case when the player types 'quit', for instance).
        """
        try:
            print(_apply_style("\n<dim>>></> ", self.do_styles), end="")
            cmd = input().lstrip()
            player.store_input_line(cmd)
            if cmd == "quit":
                return False
        except KeyboardInterrupt:
            self.break_pressed(player)
        except EOFError:
            pass
        return True

    def render_output(self, paragraphs, **params):
        """
        Render (format) the given paragraphs to a text representation.
        It doesn't output anything to the screen; it just returns the text string.
        This implementation expects 2 extra parameters: "indent" and "width".
        """
        if not paragraphs:
            return None
        indent = " " * params["indent"]
        wrapper = styleaware_wrapper.StyleTagsAwareTextWrapper(width=params["width"], fix_sentence_endings=True, initial_indent=indent, subsequent_indent=indent)
        output = []
        for txt, formatted in paragraphs:
            if formatted:
                txt = wrapper.fill(txt) + "\n"
            else:
                # unformatted output, prepend every line with the indent but otherwise leave them alone
                txt = indent + ("\n"+indent).join(txt.splitlines()) + "\n"
            assert txt.endswith("\n")
            output.append(txt)
        return "".join(output)

    def output(self, *lines):
        """Write some text to the visible output buffer."""
        for line in lines:
            print(_apply_style(line, self.do_styles))
        sys.stdout.flush()

    def output_delay(self):
        """delay the output for a short period"""
        time.sleep(self.output_line_delay / 1000.0)

    def break_pressed(self, player):
        print(_apply_style(self.CTRL_C_MESSAGE, self.do_styles))
        sys.stdout.flush()


def _apply_style(line, do_styles):
    """Convert style tags to colorama escape sequences suited for console text output"""
    if "<" not in line:
        return line
    if style_colors and do_styles:
        for tag in style_colors:
            line = line.replace("<%s>" % tag, style_colors[tag])
        return line
    else:
        return iobase.strip_text_styles(line)
