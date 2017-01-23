"""
Fallback ansi escape sequence definitions, used when 'colorama' is not installed.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

class Style(object):
    RESET_ALL = "\033[0m"
    BRIGHT = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINED = "\033[4m"
    BLINK = "\033[5m"
    REVERSEVID = "\033[7m"
    NORMAL = "\033[22m"
