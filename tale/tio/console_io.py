# coding=utf-8
"""
Console-based input/output.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import sys
import os
import signal
import locale
import threading
from . import styleaware_wrapper, iobase
try:
    from . import colorama_patched as colorama
    colorama.init()
except ImportError:
    from . import ansi_codes as colorama        # fallback

if sys.version_info < (3, 0):
    input = raw_input
else:
    input = input

__all__ = ["ConsoleIo"]

style_words = {
    "dim": colorama.Style.DIM,
    "normal": colorama.Style.NORMAL,
    "bright": colorama.Style.BRIGHT,
    "ul": colorama.Style.UNDERLINED,
    "it": colorama.Style.ITALIC,
    "rev": colorama.Style.REVERSEVID,
    "/": colorama.Style.RESET_ALL,
    "living": colorama.Style.BRIGHT,
    "player": colorama.Style.BRIGHT,
    "item": colorama.Style.BRIGHT,
    "exit": colorama.Style.BRIGHT,
    "location": colorama.Style.BRIGHT,
    "clear": "\033[1;1H\033[2J",  # ansi sequence to clear the console screen
    "monospaced": "",  # we assume the console is already monospaced font
    "/monospaced": ""
}
assert len(set(style_words.keys()) ^ iobase.ALL_STYLE_TAGS) == 0, "mismatch in list of style tags"

if sys.platform == "win32":
    if not hasattr(colorama, "win32") or colorama.win32.windll is None:
        style_words.clear()  # running on win32 without colorama ansi support

if sys.platform == "cli":
    style_words.clear()  # IronPython doesn't support console styling at all


class ConsoleIo(iobase.IoAdapterBase):
    """
    I/O adapter for the text-console (standard input/standard output).
    """
    def __init__(self, player_connection):
        super(ConsoleIo, self).__init__(player_connection)
        try:
            # try to output a unicode character such as smartypants uses for nicer formatting
            encoding = getattr(sys.stdout, "encoding", sys.getfilesystemencoding())
            if sys.version_info < (3, 0):
                unichr(8230).encode(encoding)
            else:
                chr(8230).encode(encoding)
        except (UnicodeEncodeError, TypeError):
            self.supports_smartquotes = False
        if sys.platform == "win32":
            # the windows console by default can't output nice unicode quote characters, so we disable that feature
            self.supports_smartquotes = False
        self.stop_main_loop = False
        self.input_not_paused = threading.Event()
        self.input_not_paused.set()

    def __repr__(self):
        return "<ConsoleIo @ 0x%x, local console, pid %d>" % (id(self), os.getpid())

    def singleplayer_mainloop(self, player_connection):
        """Main event loop for the console I/O adapter for single player mode"""
        while not self.stop_main_loop:
            # Input a single line of text by the player. It is stored in the internal
            # command buffer of the player. The driver's main loop can look into that
            # to see if any input should be processed.
            self.input_not_paused.wait()
            try:
                # note that we don't print any prompt ">>", that needs to be done
                # by the main thread that handles screen *output*
                # (otherwise the prompt will often appear before any regular screen output)
                old_player = player_connection.player
                cmd = input()  # blocking console input call
                if sys.version_info < (3, 0):
                    cmd = cmd.decode(sys.stdin.encoding or locale.getpreferredencoding(True))
                player_connection.player.store_input_line(cmd)
                if old_player is not player_connection.player:
                    # this situation occurs when a save game has been restored,
                    # we also have to unblock the old_player
                    old_player.store_input_line(cmd)
            except KeyboardInterrupt:
                self.break_pressed()
            except EOFError:
                pass

    def pause(self, unpause=False):
        if unpause:
            self.input_not_paused.set()
        else:
            self.input_not_paused.clear()

    def clear_screen(self):
        """Clear the screen"""
        if style_words:
            print("\033[1;1H\033[2J", end="")
        else:
            print("\n" * 5)

    def install_tab_completion(self, driver):
        """Install tab completion using readline, if available, and if not running on windows (it behaves weird)"""
        if sys.platform == "win32":
            return
        try:
            import readline
            completer = ReadlineTabCompleter(driver, self)
            readline.set_completer(completer.complete)
            if readline.__doc__ and "libedit" in readline.__doc__:
                # this is for osx pythons with libedit instead of gnu readline
                readline.parse_and_bind("bind ^I rl_complete")
            else:
                readline.parse_and_bind("tab: complete")
        except ImportError:
            return

    def abort_all_input(self, player):
        """abort any blocking input, if at all possible"""
        # This requires some drastic measures unfortunately.
        # The main thread is stuck in a blocking input (reading from stdin)
        # You really can't seem to interrupt that. So we terminate the process forcefully.
        # That will kill the whole process (including server) which is not nice in multi player mode.
        # Thankfully, the console io adapter is usually only used in single player 'if' game mode.
        player.store_input_line("")
        os.kill(os.getpid(), signal.SIGINT)

    def render_output(self, paragraphs, **params):
        """
        Render (format) the given paragraphs to a text representation.
        It doesn't output anything to the screen yet; it just returns the text string.
        Any style-tags are still embedded in the text.
        This console-implementation expects 2 extra parameters: "indent" and "width".
        """
        if not paragraphs:
            return None
        indent = " " * params["indent"]
        wrapper = styleaware_wrapper.StyleTagsAwareTextWrapper(width=params["width"], fix_sentence_endings=True, initial_indent=indent, subsequent_indent=indent)
        output = []
        for txt, formatted in paragraphs:
            if formatted:
                txt = wrapper.fill(txt) + "\n"
            else:
                # unformatted output, prepend every line with the indent but otherwise leave them alone
                txt = indent + ("\n" + indent).join(txt.splitlines()) + "\n"
            assert txt.endswith("\n")
            output.append(txt)
        return self.smartquotes("".join(output))

    def output(self, *lines):
        """Write some text to the screen. Takes care of style tags that are embedded."""
        super(ConsoleIo, self).output(*lines)
        for line in lines:
            print(self._apply_style(line, self.do_styles))
        sys.stdout.flush()

    def output_no_newline(self, text):
        """Like output, but just writes a single line, without end-of-line."""
        super(ConsoleIo, self).output_no_newline(text)
        print(self._apply_style(text, self.do_styles), end="")
        sys.stdout.flush()

    def write_input_prompt(self):
        """write the input prompt '>>'"""
        print(self._apply_style("\n<dim>>></> ", self.do_styles), end="")
        sys.stdout.flush()

    def break_pressed(self):
        """do something when the player types ctrl-C (break)"""
        if threading.current_thread().name != "MainThread":
            # ony trigger the ^C handling if we're running in the main thread,
            # otherwise we could get two triggers (one from the async i/o thread, and
            # one from the main thread)
            return
        if self.stop_main_loop:
            # don't write the feedback if the loop is already stopping
            return
        print(self._apply_style("\n* break: Use <quit> if you want to quit.", self.do_styles))
        sys.stdout.flush()

    def _apply_style(self, line, do_styles):
        """Convert style tags to ansi escape sequences suitable for console text output"""
        if "<" not in line:
            return line
        elif style_words and do_styles:
            for tag, replacement in style_words.items():
                line = line.replace("<%s>" % tag, replacement)
            return line
        else:
            return iobase.strip_text_styles(line)


class ReadlineTabCompleter(object):
    """
    Class used to provide tab-completion on the command line using readline.
    """
    def __init__(self, driver, io):
        self.driver = driver
        self.io = io
        self.candidates = []
        self.prefix = None

    def complete(self, prefix, index=None):
        if not prefix:
            return
        if prefix != self.prefix:
            # new prefix, recalculate candidates
            self.candidates = self.io.tab_complete(prefix, self.driver)
        try:
            if index is None:
                return self.candidates
            return self.candidates[index]
        except IndexError:
            return None
