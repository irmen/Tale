"""
Fallback ansi escape sequence definitions, used when 'colorama' is not installed.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""


def ansi_escapes(clazz):
    for name, code in clazz.colors.items():
        escape_seq = "\033[" + str(code) + "m"
        setattr(clazz, name, escape_seq)
    return clazz


@ansi_escapes
class Fore(object):
    colors = {
        "BLACK": 30,
        "RED": 31,
        "GREEN": 32,
        "YELLOW": 33,
        "BLUE": 34,
        "MAGENTA": 35,
        "CYAN": 36,
        "WHITE": 37,
        "RESET": 39
    }


@ansi_escapes
class Back(object):
    colors = {
        "BLACK": 40,
        "RED": 41,
        "GREEN": 42,
        "YELLOW": 43,
        "BLUE": 44,
        "MAGENTA": 45,
        "CYAN": 46,
        "WHITE": 47,
        "RESET": 49
    }


@ansi_escapes
class Style(object):
    colors = {
        "BRIGHT": 1,
        "DIM": 2,
        "UNDERLINED": 4,
        "BLINK": 5,
        "REVERSEVID": 7,
        "NORMAL": 22,
        "RESET_ALL": 0
    }
