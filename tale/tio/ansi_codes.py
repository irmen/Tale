"""
Fallback ansi escape sequence definitions, used when 'colorama' is not installed.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""


def ansi_escapes(clazz):
    for name, code in clazz.tags.items():
        escape_seq = "\033[" + str(code) + "m"
        setattr(clazz, name, escape_seq)
    return clazz


@ansi_escapes
class Style(object):
    tags = {
        "BRIGHT": 1,
        "DIM": 2,
        "ITALIC": 3,
        "UNDERLINED": 4,
        "BLINK": 5,
        "REVERSEVID": 7,
        "NORMAL": 22,
        "RESET_ALL": 0
    }
