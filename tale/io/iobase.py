"""
Basic Input/Output stuff not tied to a specific I/O implementation.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import threading
import time
from ..util import basestring_type
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
        if smartypants and self.supports_smartquotes:
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
