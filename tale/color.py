"""
Console output styling (uses colorama, no styling if not installed).

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import sys
try:
    import colorama
    colorama.init()
except ImportError:
    colorama = None


if colorama:
    BRIGHT = colorama.Style.BRIGHT
    NORMAL = colorama.Style.NORMAL
    if sys.platform == "darwin":
        DIM = ""   # mac os does not support 'dim' nicely
    else:
        DIM = colorama.Style.DIM
    RESET_ALL = colorama.Style.RESET_ALL
    def bright(txt):
        return BRIGHT+txt+NORMAL
    def dim(txt):
        return DIM+txt+NORMAL
else:
    BRIGHT = ""
    NORMAL = ""
    DIM = ""
    RESET_ALL = ""
    def bright(txt):
        return txt
    def dim(txt):
        return txt
