"""
Console-based input/output.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import sys
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


class ConsoleIo(iobase.IoAdapterBase):
    """
    I/O adapter for the text-console (standard input/standard output).
    """
    def __init__(self, config):
        super(ConsoleIo, self).__init__(config)

    def input(self, prompt=None):
        """Ask the player for immediate input."""
        print(_apply_style(prompt, self.do_styles), end="")
        return input().strip()

    def input_line(self, player):
        """
        Input a single line of text by the player. It is stored in the internal
        command buffer of the player. The driver's main loop can look into that
        to see if any input should be processed.
        This method is called from the driver's main loop (only if running in command-mode)
        or from the asynchronous input loop (if running in timer-mode).
        Returns True if the input loop should continue as usual.
        Returns False if the input loop should be terminated (this could
        be the case when the player types 'quit', for instance).
        """
        try:
            print(_apply_style("\n<dim>>></> ", self.do_styles), end="")
            cmd = input().strip()
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
        It doesn't output anything to the screen yet; it just returns the text string.
        Any style-tags are still embedded in the text.
        This console-implementation expects 2 extra parameters: "indent" and "width".
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
                txt = indent + ("\n" + indent).join(txt.splitlines()) + "\n"
            assert txt.endswith("\n")
            output.append(txt)
        return "".join(output)

    def output(self, *lines):
        """Write some text to the screen. Needs to take care of style tags that are embedded."""
        for line in lines:
            print(_apply_style(line, self.do_styles))
        sys.stdout.flush()

    def break_pressed(self, player):
        """do something when the player types ctrl-C (break)"""
        print(_apply_style("\n* break: Use <quit> if you want to quit.", self.do_styles))
        sys.stdout.flush()


def _apply_style(line, do_styles):
    """Convert style tags to colorama escape sequences suitable for console text output"""
    if "<" not in line:
        return line
    if style_colors and do_styles:
        for tag in style_colors:
            line = line.replace("<%s>" % tag, style_colors[tag])
        return line
    else:
        return iobase.strip_text_styles(line)
