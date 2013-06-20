"""
Basic Input/Output stuff not tied to a specific I/O implementation.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import threading
import time
from ..util import basestring_type
from .. import soul
try:
    import mdx_smartypants
    smartypants = mdx_smartypants.spants
except ImportError:
    try:
        import smartypants
    except ImportError:
        smartypants = None
try:
    import HTMLParser
    unescape_entity = HTMLParser.HTMLParser().unescape
except ImportError:
    import html.parser
    unescape_entity = html.parser.HTMLParser().unescape


ALL_COLOR_TAGS = {
    "dim", "normal", "bright", "ul", "rev", "blink", "/",
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
    "bg:black", "bg:red", "bg:green", "bg:yellow", "bg:blue", "bg:magenta", "bg:cyan", "bg:white",
    "living", "player", "item", "exit", "location", "monospaced", "/monospaced"
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


class AsyncPlayerInput(threading.Thread):
    """
    Input-task that runs asynchronously (background thread).
    This is used by the driver when running in timer-mode, where the driver's
    main loop needs to run separated from this input thread.
    """
    def __init__(self, player):
        super(AsyncPlayerInput, self).__init__()
        self.player = player
        self.daemon = True
        self.name = "async-input"
        self.enabled = threading.Event()
        self.enabled.clear()
        self._stoploop = False
        self.start()

    def run(self):
        loop = True
        while loop:
            self.enabled.wait()
            if self._stoploop:
                break
            loop = self.player.io.input_line(self.player)
            self.enabled.clear()

    def enable(self):
        if self._stoploop:
            raise SystemExit()
        self.enabled.set()

    def stop(self):
        self._stoploop = True
        self.enabled.set()
        self.player.io.break_input_line()


class IoAdapterBase(object):
    """
    I/O adapter base class
    """
    def __init__(self, config):
        self.output_line_delay = 50   # milliseconds. (will be overwritten by the game driver)
        self.do_styles = True
        self.do_smartquotes = True
        self.supports_smartquotes = True

    def get_async_input(self, player):
        """
        Get the object that is reading the player's input, asynchronously from the driver's main loop.
        Make sure that the object is active (i.e. restart it if it has been stopped in the meantime).
        """
        return AsyncPlayerInput(player)

    def mainloop_threads(self, driver_mainloop):
        """
        Return a tuple (driver_mainloop_thread, io_adapter_mainloop_callable).
        The driver_mainloop_thread is the thread object to run the driver mainloop in. If it is None,
        the driver mainloop is just executed in the main thread (the second field of the tuple must be None too).
        If the driver_mainloop_thread is a thread object, it is used for the driver main loop.
        The io_adapter_mainloop_callable will be run in the application's main thread instead.
        """
        return None, None

    def destroy(self):
        """Called when the I/O adapter is shut down"""
        pass

    def clear_screen(self):
        """Clear the screen"""
        pass

    def install_tab_completion(self, completer):
        """Install and enable tab-command-completion if possible"""
        pass

    def critical_error(self, message="Critical Error. Shutting down."):
        """called when the driver encountered a critical error and the session needs to shut down"""
        import traceback, sys
        tb = traceback.format_exc()
        print(message, file=sys.stderr)
        print(tb, file=sys.stderr)

    def input(self, prompt=None):
        """
        Ask the player for immediate input. The input is not stored, but returned immediately.
        (Don't call this directly, use player.input)
        """
        raise NotImplementedError("implement this in subclass")

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
        raise NotImplementedError("implement this in subclass")

    def break_input_line(self):
        """break a pending input_line, if possible"""
        pass

    def render_output(self, paragraphs, **params):
        """
        Render (format) the given paragraphs to a text representation.
        It doesn't output anything to the screen yet; it just returns the text string.
        Any style-tags are still embedded in the text.
        This console-implementation expects 2 extra parameters: "indent" and "width".
        """
        raise NotImplementedError("implement this in subclass")

    def smartquotes(self, text):
        """Apply 'smart quotes' to the text; replaces quotes and dashes by nicer looking symbols"""
        if smartypants and self.supports_smartquotes and self.do_smartquotes:
            return unescape_entity(smartypants.smartyPants(text))
        return text

    def output(self, *lines):
        """Write some text to the screen. Needs to take care of style tags that are embedded."""
        raise NotImplementedError("implement this in subclass")

    def break_pressed(self, player):
        """do something when the player types ctrl-C (break)"""
        pass

    def output_delay(self):
        """delay the output for a short period"""
        time.sleep(self.output_line_delay / 1000.0)


class TabCompleter(object):
    """
    Class used to provide tab-completion on the command line.
    """
    def __init__(self, driver, player):
        self.driver = driver
        self.player = player
        self.candidates=[]
        self.prefix=None
    def complete(self, prefix, index=None):
        if not prefix:
            return
        if prefix != self.prefix:
            # new prefix, recalculate candidates
            verbs = [verb for verb in self.driver.get_current_verbs() if verb.startswith(prefix)]
            livings = [living.name for living in self.player.location.livings if living.name.startswith(prefix)]
            livings_aliases = [alias for living in self.player.location.livings for alias in living.aliases if alias.startswith(prefix)]
            items = [item.name for item in self.player.location.items if item.name.startswith(prefix)]
            items_aliases = [alias for item in self.player.location.items for alias in item.aliases if alias.startswith(prefix)]
            exits = [exit for exit in self.player.location.exits if exit.startswith(prefix)]
            inventory = [item.name for item in self.player.inventory if item.name.startswith(prefix)]
            inventory_aliases = [alias for item in self.player.inventory for alias in item.aliases if alias.startswith(prefix)]
            emotes = [verb for verb in soul.VERBS if verb.startswith(prefix)]
            self.candidates = sorted(verbs+livings+items+exits+inventory+emotes+livings_aliases+items_aliases+inventory_aliases)
        try:
            if index is None:
                return self.candidates
            return self.candidates[index]
        except IndexError:
            return None
