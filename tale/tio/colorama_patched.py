"""
Monkeypatch colorama to support a few additional text styles

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""


def monkeypatch_extra_styles():
    import colorama

    # patch in a few extra ansi styles
    if not hasattr(colorama.ansi.AnsiStyle, "ITALIC"):
        colorama.ansi.AnsiStyle.ITALIC = 3
        colorama.ansi.AnsiStyle.UNDERLINED = 4
        colorama.ansi.AnsiStyle.BLINK = 5
        colorama.ansi.AnsiStyle.REVERSEVID = 7
        colorama.ansi.Style = colorama.Style = colorama.ansi.AnsiStyle()

    # Patch in a trick to use reverse video on windows console (where REVERSEVID doesn't work natively)
    if colorama.ansitowin32.winterm is not None:
        orig_get_win32_calls = colorama.ansitowin32.AnsiToWin32.get_win32_calls

        def monkeypatched_get_win32_calls(self, **args):
            def style_reverse_vid(on_stderr=None, **args):
                term = colorama.ansitowin32.winterm
                term._fore, term._back = term._back, term._fore
                term.set_console(on_stderr=on_stderr)
            result = orig_get_win32_calls(self, **args)
            result[colorama.ansi.AnsiStyle.REVERSEVID] = (style_reverse_vid,)
            return result

        colorama.ansitowin32.AnsiToWin32.get_win32_calls = monkeypatched_get_win32_calls


monkeypatch_extra_styles()
del monkeypatch_extra_styles
from colorama import init, Style, Fore, Back

try:
    from colorama import win32, ansitowin32
except ImportError:
    pass


if __name__ == "__main__":
    init()
    print("\x1b[1;1H\x1b[2J------------colorama test (clear screen)-------------")
    print(Style.BRIGHT + "bright" + Style.RESET_ALL)
    print(Style.UNDERLINED + "underlined" + Style.RESET_ALL)
    print(Style.BLINK + "blink" + Style.RESET_ALL)
    print(Style.ITALIC + "italic" + Style.RESET_ALL)
    print(Fore.YELLOW + Back.RED + "yellow on red" + Style.RESET_ALL)
    print(Style.REVERSEVID + "reversevid" + Style.RESET_ALL)
    print(Fore.YELLOW + Back.RED + Style.REVERSEVID + "yellow on red, reversed" + Style.RESET_ALL)
