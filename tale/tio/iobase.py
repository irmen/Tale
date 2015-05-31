# coding=utf-8
"""
Basic Input/Output stuff not tied to a specific I/O implementation.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import sys
import traceback
from ..util import basestring_type
from .. import soul
try:
    import HTMLParser
    unescape_entity = HTMLParser.HTMLParser().unescape
except ImportError:
    import html.parser
    if hasattr(html.parser, "unescape"):
        unescape_entity = html.parser.unescape  # 3.4+
    else:
        unescape_entity = html.parser.HTMLParser().unescape
import smartypants
smartypants.process_escapes = lambda txt: txt  # disable the escape processing
smartypants = smartypants.smartypants

ALL_STYLE_TAGS = {
    "dim", "normal", "bright", "ul", "it", "rev", "clear", "/",
    "living", "player", "item", "exit", "location", "monospaced", "/monospaced"
}


def strip_text_styles(text):
    """remove any special text styling tags from the text (you can pass a single string, and also a list of strings)"""
    def strip(text):
        if "<" not in text:
            return text
        for tag in ALL_STYLE_TAGS:
            text = text.replace("<%s>" % tag, "")
        return text
    if isinstance(text, basestring_type):
        return strip(text)
    return [strip(line) for line in text]


class IoAdapterBase(object):
    """
    I/O adapter base class
    """
    def __init__(self, player_connection):
        self.do_styles = True
        self.do_smartquotes = True
        self.supports_smartquotes = True
        self.supports_blocking_input = True
        self.player_connection = player_connection
        self.stop_main_loop = False
        self.last_output_line = None

    def destroy(self):
        """Called when the I/O adapter is shut down"""
        pass

    def singleplayer_mainloop(self, player_connection):
        """Main event loop for this I/O adapter for single player mode"""
        raise NotImplementedError("implement this in subclass")

    def clear_screen(self):
        """Clear the screen"""
        pass

    def critical_error(self, message="Critical Error. Shutting down."):
        """called when the driver encountered a critical error and the session needs to shut down"""
        tb = traceback.format_exc()
        print(message, file=sys.stderr)
        print(tb, file=sys.stderr)

    def abort_all_input(self, player):
        """abort any blocking input, if at all possible"""
        pass

    def render_output(self, paragraphs, **params):
        """
        Render (format) the given paragraphs to a text representation.
        It doesn't output anything to the screen yet; it just returns the text string.
        Any style-tags are still embedded in the text.
        This console-implementation expects 2 extra parameters: "indent" and "width".
        """
        raise NotImplementedError("implement this in subclass")

    def smartquotes(self, text, escaped_entities=False):
        """Apply 'smart quotes' to the text; replaces quotes and dashes by nicer looking symbols"""
        if self.supports_smartquotes and self.do_smartquotes:
            quoted = smartypants(text)
            if escaped_entities:
                return quoted
            return unescape_entity(quoted)
        return text

    def output(self, *lines):
        """
        Write some text to the screen. Needs to take care of style tags that are embedded.
        Implement specific behavior in subclass (but don't forget to call base method)
        """
        self.last_output_line = lines[-1]

    def output_no_newline(self, text):
        """
        Like output, but just writes a single line, without end-of-line.
        Implement specific behavior in subclass (but don't forget to call base method)
        """
        self.last_output_line = text

    def write_input_prompt(self):
        """write the input prompt '>>'"""
        pass

    def break_pressed(self):
        """do something when the player types ctrl-C (break)"""
        pass

    def pause(self, unpause=False):
        """pause/ unpause the input loop"""
        raise NotImplementedError("implement this in subclass")

    def tab_complete(self, prefix, driver):
        if not prefix:
            return
        prefix = prefix.lower()
        player = self.player_connection.player
        verbs = [verb for verb in driver.current_verbs(player) if verb.startswith(prefix)]
        livings = [living.name for living in player.location.livings if living.name.startswith(prefix)]
        livings_aliases = [alias for living in player.location.livings for alias in living.aliases if alias.startswith(prefix)]
        items = [item.name for item in player.location.items if item.name.startswith(prefix)]
        items_aliases = [alias for item in player.location.items for alias in item.aliases if alias.startswith(prefix)]
        exits = [xt for xt in player.location.exits if xt.startswith(prefix)]
        inventory = [item.name for item in player.inventory if item.name.startswith(prefix)]
        inventory_aliases = [alias for item in player.inventory for alias in item.aliases if alias.startswith(prefix)]
        emotes = [verb for verb in soul.VERBS if verb.startswith(prefix)]
        self.candidates = sorted(verbs + livings + items + exits + inventory + emotes + livings_aliases + items_aliases + inventory_aliases)
        return self.candidates
