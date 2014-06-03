"""
Monkeypatch colorama to support a few additional text styles

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import sys
from .. import util
import colorama
import colorama.ansi
import colorama.winterm
import colorama.ansitowin32
import colorama.win32

# version check
colorama_version = util.version_tuple(getattr(colorama, "VERSION", None) or getattr(colorama, "__version__"))
if colorama_version < (0, 3, 1):
    import warnings
    warnings.warn("Incompatible colorama version {0} found, need at least 0.3.1".format(colorama_version), RuntimeWarning)
    raise ImportError("not using colorama")

# patch in extra ansi styles
colorama.ansi.AnsiStyle.UNDERLINED = 4
colorama.ansi.AnsiStyle.BLINK = 5
colorama.ansi.AnsiStyle.REVERSEVID = 7
colorama.ansi.Style = colorama.ansi.AnsiCodes(colorama.ansi.AnsiStyle)
colorama.Style = colorama.ansi.Style

# patch windows stuff, if running on windows
if colorama.win32.windll is not None:

    class MonkeypatchedAnsiToWin32(colorama.ansitowin32.AnsiToWin32):
        def get_win32_calls(self):
            result = super(MonkeypatchedAnsiToWin32, self).get_win32_calls() or {}
            result[colorama.ansi.AnsiStyle.REVERSEVID] = (self.style_reverse_vid, )
            return result

        def style_reverse_vid(self, style=None, on_stderr=False):
            # Reverse-video style doesn't seem to work on windows, so we simulate it:
            # flip foreground and background colors.
            term = colorama.ansitowin32.winterm
            term._fore, term._back = term._back, term._fore
            term.set_console(on_stderr=on_stderr)

    colorama.win32.COORD = colorama.win32.wintypes._COORD

    if sys.version_info >= (3, 0):
        # this function is mixing up bytes/str/int on Python 2.x/3.x, patch it
        __orig_FillConsoleOutputCharacter = colorama.win32.FillConsoleOutputCharacter
        def Monkeypatched_FillConsoleOutputCharacter(stream_id, char, length, start):
            if type(char) is str:
                char = char.encode("ascii")
            elif type(char) is int:
                char = bytes([char])
            __orig_FillConsoleOutputCharacter(stream_id, char, length, start)

        import colorama.initialise
        colorama.win32.FillConsoleOutputCharacter = Monkeypatched_FillConsoleOutputCharacter
    colorama.ansitowin32.AnsiToWin32 = MonkeypatchedAnsiToWin32
    colorama.initialise.AnsiToWin32 = colorama.ansitowin32.AnsiToWin32
    colorama.AnsiToWin32 = colorama.ansitowin32.AnsiToWin32


from colorama import *

if __name__ == "__main__":
    colorama.init()
    print("\x1b[1;1H\x1b[2J-----------------colorama test----------------")
    print(colorama.Style.BRIGHT + "bright" + colorama.Style.RESET_ALL)
    print(colorama.Style.UNDERLINED + "underlined" + colorama.Style.RESET_ALL)
    print(colorama.Style.BLINK + "blink" + colorama.Style.RESET_ALL)
    print(colorama.Fore.YELLOW + colorama.Back.RED + "yellow on red" + colorama.Style.RESET_ALL)
    print(colorama.Style.REVERSEVID + "reversevid" + colorama.Style.RESET_ALL)
    print(colorama.Fore.YELLOW + colorama.Back.RED + colorama.Style.REVERSEVID + "yellow on red, reversed" + colorama.Style.RESET_ALL)
