"""
Fallback ansi escape sequence definitions, used when 'colorama' is not installed.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""


def _escapeseq(code):
    return "\033[" + str(code) + "m"


class Fore(object):
    BLACK   = _escapeseq(30)
    RED     = _escapeseq(31)
    GREEN   = _escapeseq(32)
    YELLOW  = _escapeseq(33)
    BLUE    = _escapeseq(34)
    MAGENTA = _escapeseq(35)
    CYAN    = _escapeseq(36)
    WHITE   = _escapeseq(37)
    RESET   = _escapeseq(39)


class Back(object):
    BLACK   = _escapeseq(40)
    RED     = _escapeseq(41)
    GREEN   = _escapeseq(42)
    YELLOW  = _escapeseq(43)
    BLUE    = _escapeseq(44)
    MAGENTA = _escapeseq(45)
    CYAN    = _escapeseq(46)
    WHITE   = _escapeseq(47)
    RESET   = _escapeseq(49)


class Style(object):
    BRIGHT      = _escapeseq(1)
    DIM         = _escapeseq(2)
    UNDERLINED  = _escapeseq(4)
    BLINK       = _escapeseq(5)
    REVERSEVID  = _escapeseq(7)
    NORMAL      = _escapeseq(22)
    RESET_ALL   = _escapeseq(0)
