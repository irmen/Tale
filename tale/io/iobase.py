"""
Basic Input/Output stuff not tied to a specific I/O implementation.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
from ..util import basestring_type


ALL_COLOR_TAGS = {
    "dim", "normal", "bright", "ul", "rev", "blink", "/",
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
    "bg:black", "bg:red", "bg:green", "bg:yellow", "bg:blue", "bg:magenta", "bg:cyan", "bg:white",
    "living", "player", "item", "exit", "location"
}


def strip_text_styles(text):
    """remove any special text styling tags from the text (you can pass a single string, and also a list of strings)"""
    def strip(text):
        if "<" not in text:
            return text
        for tag in ALL_COLOR_TAGS:
            text = text.replace("<%s>" % tag, "")
        return text
    if isinstance(text, basestring_type):
        return strip(text)
    return [strip(line) for line in text]
