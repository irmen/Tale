"""
GUI input/output using Tkinter.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import sys
import re
import textwrap
import collections
import threading
try:
    from tkinter import *
    import tkinter.font as tkfont
    import tkinter.messagebox as tkmsgbox
except ImportError:
    from Tkinter import *
    import tkFont as tkfont
    import tkMessageBox as tkmsgbox
from . import iobase, vfs
from .. import mud_context
from .. import __version__ as tale_version

__all__ = ["TkinterIo"]


class TkinterIo(iobase.IoAdapterBase):
    """
    Tkinter-GUI based Input/Output adapter.
    """
    def __init__(self, config):
        super(TkinterIo, self).__init__(config)
        self.gui = TaleGUI(self, config)
        self.textwrapper = textwrap.TextWrapper()

    def mainloop(self):
        """Main event loop for this I/O adapter"""
        self.gui.mainloop()

    def clear_screen(self):
        """Clear the screen"""
        self.gui.clear_screen()

    def critical_error(self, message="Critical Error. Shutting down."):
        """called when the driver encountered a critical error and the session needs to shut down"""
        super(TkinterIo, self).critical_error(message)
        import traceback
        tb = traceback.format_exc()
        self.output("<bright><red>%s</>\n" % message)
        self.output("<rev>" + tb + "</>")
        self.output("<red>All you can do now is close this window... Sorry for the inconvenience.</>")

    def install_tab_completion(self, completer):
        self.gui.install_tab_completion(completer)

    def destroy(self):
        self.gui.destroy()

    def gui_terminated(self):
        self.gui = None

    def abort_all_input(self, player):
        """abort any blocking input, if at all possible"""
        player.store_input_line("")

    def render_output(self, paragraphs, **params):
        """
        Render (format) the given paragraphs to a text representation.
        It doesn't output anything to the screen yet; it just returns the text string.
        Any style-tags are still embedded in the text.
        This tkinter-implementation expects no extra parameters.
        """
        if not paragraphs:
            return None
        output = []
        for txt, formatted in paragraphs:
            if formatted:
                # formatted output, munge whitespace (like the console text output does)
                txt = self.textwrapper._munge_whitespace(txt) + "\n"
            else:
                # unformatted paragraph, just leave the text as-is (don't textwrap it)
                pass
            assert txt.endswith("\n")
            output.append(txt)
        return self.smartquotes("".join(output))

    def output(self, *lines):
        """Write some text to the screen. Needs to take care of style tags that are embedded."""
        for line in lines:
            self.gui.write_line(line)

    def output_no_newline(self, text):
        """Like output, but just writes a single line, without end-of-line."""
        self.gui.write_line(text)


class TaleWindow(Toplevel):
    """The actual gui-window, containing the output text and the input command bar."""
    def __init__(self, gui, parent, title, text, modal=False):
        Toplevel.__init__(self, parent)
        self.gui = gui
        self.configure(borderwidth=5)
        self.geometry("=%dx%d+%d+%d" % (800, 600,
                                        parent.winfo_rootx() + 10,
                                        parent.winfo_rooty() + 10))
        self.bg = '#f8f8f0'
        self.fg = '#080808'
        self.fontsize_monospace = 11
        self.fontsize_normal = 11
        if sys.platform == "darwin":
            self.fontsize_monospace += 3
            self.fontsize_normal += 5
        self.font = self.FindFont(['Georgia', 'DejaVu Serif', 'Droid Serif', 'Times New Roman', 'Times', 'Serif'], self.fontsize_normal)
        self.boldFond = self.FindFont(['Georgia', 'DejaVu Serif', 'Droid Serif', 'Times New Roman', 'Times', 'Serif'], self.fontsize_normal, weight=tkfont.BOLD)
        self.underlinedFond = self.FindFont(['Georgia', 'DejaVu Serif', 'Droid Serif', 'Times New Roman', 'Times', 'Serif'], self.fontsize_normal, underlined=True)
        self.CreateWidgets()
        self.title(title)
        self.protocol("WM_DELETE_WINDOW", self.quit_button_clicked)
        self.parent = parent
        self.textView.focus_set()
        #key bindings for this dialog
        #self.bind('<Return>',self.Ok) #dismiss dialog
        #self.bind('<Escape>',self.Ok) #dismiss dialog
        self.textView.insert(0.0, text)
        self.textView.config(state=DISABLED)

        with vfs.vfs.open_read("io/quill_pen_paper.gif") as icon:
            img = PhotoImage(file=icon.name)
            self.tk.call('wm', 'iconphoto', self, img)
            #self.iconbitmap(name)

        self.history = collections.deque(maxlen=100)
        self.history.append("")
        self.history_idx = 0
        if modal:
            self.transient(parent)
            self.grab_set()
            self.wait_window()
        self.update_lock = threading.Lock()

    def CreateWidgets(self):
        frameText = Frame(self, relief=SUNKEN, height=700)
        frameCommands = Frame(self, relief=SUNKEN)
        self.scrollbarView = Scrollbar(frameText, orient=VERTICAL, takefocus=FALSE, highlightthickness=0)
        self.textView = Text(frameText, wrap=WORD, highlightthickness=0, fg=self.fg, bg=self.bg, font=self.font, padx=8, pady=8)
        self.scrollbarView.config(command=self.textView.yview)
        self.textView.config(yscrollcommand=self.scrollbarView.set)

        self.commandPrompt = Label(frameCommands, text="> ")
        fixedFont = self.FindFont(["Consolas", "Lucida Console", "DejaVu Sans Mono"], self.fontsize_monospace)
        if not fixedFont:
            fixedFont = tkfont.nametofont('TkFixedFont').copy()
            fixedFont["size"] = self.fontsize_monospace
        self.commandEntry = Entry(frameCommands, takefocus=TRUE, font=fixedFont)
        self.commandEntry.bind('<Return>', self.user_cmd)
        self.commandEntry.bind('<Extended-Return>', self.user_cmd)
        self.commandEntry.bind('<KP_Enter>', self.user_cmd)
        self.commandEntry.bind('<F1>', self.f1_pressed)
        self.commandEntry.bind('<Up>', self.up_pressed)
        self.commandEntry.bind('<Down>', self.down_pressed)
        self.scrollbarView.pack(side=RIGHT, fill=Y)
        self.textView.pack(side=LEFT, expand=TRUE, fill=BOTH)
        # configure the text tags
        self.textView.tag_configure('userinput', font=fixedFont, foreground='maroon', spacing1=10, spacing3=4, lmargin1=20, lmargin2=20, rmargin=20)
        self.textView.tag_configure('dim', foreground='brown')
        self.textView.tag_configure('bright', foreground='black', font=self.boldFond)
        self.textView.tag_configure('ul', foreground='black', font=self.underlinedFond)
        self.textView.tag_configure('rev', foreground=self.bg, background=self.fg)
        self.textView.tag_configure('living', foreground='black', font=self.boldFond)
        self.textView.tag_configure('player', foreground='black', font=self.boldFond)
        self.textView.tag_configure('item', foreground='black', font=self.boldFond)
        self.textView.tag_configure('exit', foreground='black', font=self.boldFond)
        self.textView.tag_configure('location', foreground='navy', font=self.boldFond)
        self.textView.tag_configure('monospaced', font=fixedFont)
        self.textView.tag_configure('black', foreground='black')
        self.textView.tag_configure('red', foreground='red')
        self.textView.tag_configure('green', foreground='green')
        self.textView.tag_configure('yellow', foreground='yellow')
        self.textView.tag_configure('blue', foreground='blue')
        self.textView.tag_configure('magenta', foreground='magenta')
        self.textView.tag_configure('cyan', foreground='cyan')
        self.textView.tag_configure('white', foreground='white')
        self.textView.tag_configure('bg:black', background='black')
        self.textView.tag_configure('bg:red', background='red')
        self.textView.tag_configure('bg:green', background='green')
        self.textView.tag_configure('bg:yellow', background='yellow')
        self.textView.tag_configure('bg:blue', background='blue')
        self.textView.tag_configure('bg:magenta', background='magenta')
        self.textView.tag_configure('bg:cyan', background='cyan')
        self.textView.tag_configure('bg:white', background='white')

        # pack
        self.commandPrompt.pack(side=LEFT)
        self.commandEntry.pack(side=LEFT, expand=TRUE, fill=X, ipady=1)
        frameText.pack(side=TOP, expand=TRUE, fill=BOTH)
        frameCommands.pack(side=BOTTOM, fill=X)
        self.commandEntry.focus_set()

    def FindFont(self, families, size, weight=tkfont.NORMAL, slant=tkfont.ROMAN, underlined=False):
        fontfamilies = tkfont.families()
        for family in families:
            if family in fontfamilies:
                return tkfont.Font(family=family, size=size, weight=weight, slant=slant, underline=underlined)
        return None

    def f1_pressed(self, e):
        self.commandEntry.delete(0, END)
        self.commandEntry.insert(0, "help")
        self.commandEntry.event_generate("<Return>")

    def up_pressed(self, e):
        self.history_idx = max(0, self.history_idx - 1)
        if self.history_idx < len(self.history):
            self.commandEntry.delete(0, END)
            self.commandEntry.insert(0, self.history[self.history_idx])

    def down_pressed(self, e):
        self.history_idx = min(len(self.history) - 1, self.history_idx + 1)
        if self.history_idx < len(self.history):
            self.commandEntry.delete(0, END)
            self.commandEntry.insert(0, self.history[self.history_idx])

    def user_cmd(self, e):
        cmd = self.commandEntry.get().strip()
        if cmd:
            self.write_line("", self.gui.io.do_styles)
            self.write_line("<userinput>%s</>" % cmd, True)
        self.gui.register_cmd(cmd)
        self.commandEntry.delete(0, END)
        if cmd:
            if cmd != self.history[-1]:
                self.history.append(cmd)
            self.history_idx = len(self.history)

    def clear_text(self):
        with self.update_lock:
            self.textView.config(state=NORMAL)
            self.textView.delete(1.0, END)
            self.textView.config(state=DISABLED)

    def write_line(self, line, do_styles):
        with self.update_lock:
            if do_styles:
                words = re.split(r"(<\S+?>)", line)
                self.textView.config(state=NORMAL)
                tag = None
                for word in words:
                    match = re.match(r"<(\S+?)>$", word)
                    if match:
                        tag = match.group(1)
                        if tag == "monospaced":
                            self.textView.mark_set("begin_monospaced", INSERT)
                            self.textView.mark_gravity("begin_monospaced", LEFT)
                        elif tag == "/monospaced":
                            self.textView.tag_add("monospaced", "begin_monospaced", INSERT)
                            tag = None
                        elif tag == "/":
                            tag = None
                        continue
                    self.textView.insert(END, word, tag)        # @todo this can't deal yet with combined styles
                self.textView.insert(END, "\n")
                self.textView.config(state=DISABLED)
            else:
                line = iobase.strip_text_styles(line)
                self.textView.config(state=NORMAL)
                self.textView.insert(END, line + "\n")
                self.textView.config(state=DISABLED)
            self.textView.yview(END)

    def quit_button_clicked(self, event=None):
        quit = tkmsgbox.askokcancel("Quit Confirmation", "Quitting like this will abort your game.\nYou will lose your progress. Are you sure?", master=self)
        if quit:
            self.gui.destroy(True)
            self.gui.window_closed()

    def disable_input(self):
        self.commandEntry.config(state=DISABLED)


class TaleGUI(object):
    """Helper class to set up the gui and connect events."""
    def __init__(self, io, config):
        self.io = io
        self.server_config = config
        self.root = Tk()
        window_title = "{name}  {version}  |  Tale IF {taleversion}".format(
            name=self.server_config.name,
            version=self.server_config.version,
            taleversion=tale_version
        )
        self.root.title(window_title)
        self.window = TaleWindow(self, self.root, window_title, "")
        self.root.withdraw()
        self.root.update()

    def install_tab_completion(self, completer):
        def tab_pressed(event):
            begin, _, prefix = event.widget.get().rpartition(" ")
            candidates = completer.complete(prefix=prefix)
            if candidates:
                if len(candidates) == 1:
                    # replace text by the only possible candidate
                    event.widget.delete(0, END)
                    if begin:
                        event.widget.insert(0, begin + " " + candidates[0] + " ")
                    else:
                        event.widget.insert(0, candidates[0] + " ")
                else:
                    self.write_line("\n<ul>possible words:</> ")
                    self.write_line("<monospaced>" + "   ".join(candidates) + "</>\n")
            return "break"  # stop event propagation
        self.window.commandEntry.bind('<Tab>', tab_pressed)

    def mainloop(self):
        self.root.mainloop()
        self.window = None
        self.root = None
        self.io.gui_terminated()

    def destroy(self, force=False):
        def destroy2():
            self.window.destroy()
            self.root.destroy()
            self.window = None
            self.root = None
        if self.window:
            self.window.disable_input()
        if force:
            destroy2()
        elif self.root:
            self.root.after(2000, destroy2)

    def window_closed(self):
        mud_context.driver.stop_driver()

    def clear_screen(self):
        if self.root:
            self.root.after_idle(lambda: self.window.clear_text())

    def write_line(self, line):
        if self.root:
            self.root.after_idle(lambda: self.window.write_line(line, self.io.do_styles))

    def register_cmd(self, cmd):
        mud_context.player.store_input_line(cmd)


def show_error_dialog(title, message):
    """show a modal error dialog"""
    root = Tk()
    root.withdraw()
    tkmsgbox.showerror(title, message)
    root.destroy()
