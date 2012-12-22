"""
GUI input/output using Tkinter.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
import threading
import sys
import textwrap
try:
    from tkinter import *
    import tkinter.font as tkfont
    import tkinter.messagebox as tkmsgbox
except ImportError:
    from Tkinter import *
    import tkFont as tkfont
    import tkMessageBox as tkmsgbox
from . import iobase, vfs
from .. import globalcontext
from ..util import queue
from .. import __version__ as tale_version

__all__ = ["TkinterIo"]


class TkinterIo(iobase.IoAdapterBase):
    """
    Tkinter-GUI based Input/Output adapter.
    """
    def __init__(self, config):
        super(TkinterIo, self).__init__(config)
        self.cmd_queue = queue.Queue()
        self.gui = TaleGUI(self, config)
        self.player = None
        self.textwrapper = textwrap.TextWrapper()

    def mainloop_threads(self, driver_mainloop):
        driver_thread = threading.Thread(name="driver", target=driver_mainloop)
        driver_thread.daemon = True
        driver_thread.name = "driver"
        return driver_thread, self.gui.mainloop

    def destroy(self):
        self.gui.destroy()

    def gui_terminated(self):
        self.gui = None

    def input(self, prompt=None):
        """Ask the player for immediate input."""
        prompt = _apply_style(prompt, self.do_styles)
        self.gui.write_line(prompt)
        return self.cmd_queue.get().strip()

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
        cmd = self.cmd_queue.get().strip()
        player.store_input_line(cmd)
        if cmd == "quit":
            return False
        return True

    def break_input_line(self):
        """break a pending input_line, if possible"""
        self.cmd_queue.put("")

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
                # unformatted paragraph, just copy the text as is ?
                pass
            assert txt.endswith("\n")
            output.append(txt)
        return self.smartquotes("".join(output))

    def output(self, *lines):
        """Write some text to the screen. Needs to take care of style tags that are embedded."""
        for line in lines:
            line = _apply_style(line, self.do_styles)
            self.gui.write_line(line)


def _apply_style(line, do_styles):      # @TODO
    """Convert style tags to Tkinter stuff"""
    if "<" not in line:
        return line
    return iobase.strip_text_styles(line)


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

        with vfs.vfs.open_read("io/quill_pen_paper.ico") as icon:
            self.iconbitmap(icon.name)
        if modal:
            self.transient(parent)
            self.grab_set()
            self.wait_window()

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
        self.scrollbarView.pack(side=RIGHT, fill=Y)
        self.textView.pack(side=LEFT, expand=TRUE, fill=BOTH)
        self.textView.tag_configure('userinput', font=fixedFont, foreground='maroon', spacing1=10, spacing3=4, lmargin1=20, lmargin2=20, rmargin=20)
        self.commandPrompt.pack(side=LEFT)
        self.commandEntry.pack(side=LEFT, expand=TRUE, fill=X, ipady=1)

        frameText.pack(side=TOP, expand=TRUE, fill=BOTH)
        frameCommands.pack(side=BOTTOM, fill=X)
        self.commandEntry.focus_set()

    def FindFont(self, families, size):
        fontfamilies = tkfont.families()
        for family in families:
            if family in fontfamilies:
                return tkfont.Font(family=family, size=size)
        return None

    def f1_pressed(self, e):
        self.commandEntry.delete(0, END)
        self.commandEntry.insert(0, "help")
        self.commandEntry.event_generate("<Return>")

    def user_cmd(self, e):
        cmd = self.commandEntry.get()
        self.write_line("")
        self.write_line(cmd, tag="userinput")
        self.gui.register_cmd(cmd)
        self.commandEntry.delete(0, END)

    def write_line(self, line, tag=None):
        self.textView.config(state=NORMAL)
        self.textView.insert(END, line + "\n", tag)
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
        self.cmd_queue = queue.Queue()
        self.root = Tk()
        window_title = "{name}  {version}  |  Tale IF {taleversion}".format(
            name=self.server_config.name,
            version=self.server_config.version,
            taleversion=tale_version
        )
        self.root.title(window_title)
        self.root.bind("<<process_tale_command>>", self.root_process_cmd)
        self.window = TaleWindow(self, self.root, window_title, "\n\n")
        self.gui_ready = threading.Event()
        self.root.withdraw()
        self.root.update()

    def mainloop(self):
        self.root.after(100, lambda: self.gui_ready.set())
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
        self.window.disable_input()
        if force:
            destroy2()
        else:
            self.root.after(2000, destroy2)

    def window_closed(self):
        globalcontext.mud_context.driver.stop_driver()

    def root_process_cmd(self, event):
        line = self.cmd_queue.get()
        self.window.write_line(line)

    def write_line(self, line):
        self.gui_ready.wait()
        if self.root:
            # We put the input data in a queue and generate a virtual envent for the Tk root window.
            # The event handler runs in the correct thread and grabs the data from the queue.
            self.cmd_queue.put(line)
            self.root.event_generate("<<process_tale_command>>", when='tail')

    def register_cmd(self, cmd):
        self.io.cmd_queue.put(cmd)
