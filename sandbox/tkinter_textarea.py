from Tkinter import *
import tkFont
import tkMessageBox

class TextViewer(Toplevel):
    def __init__(self, parent, title, text, modal=True):
        Toplevel.__init__(self, parent)
        self.configure(borderwidth=5)
        self.geometry("=%dx%d+%d+%d" % (800, 600,
                                        parent.winfo_rootx() + 10,
                                        parent.winfo_rooty() + 10))
        self.bg = '#f8f8f0'
        self.fg = '#080808'
        self.font = ('DejaVu serif', 11)

        self.CreateWidgets()
        self.title(title)
        self.protocol("WM_DELETE_WINDOW", self.Ok)
        self.parent = parent
        self.textView.focus_set()
        #key bindings for this dialog
        #self.bind('<Return>',self.Ok) #dismiss dialog
        #self.bind('<Escape>',self.Ok) #dismiss dialog
        self.textView.insert(0.0, text)
        self.textView.config(state=DISABLED)

        if modal:
            self.transient(parent)
            self.grab_set()
            self.wait_window()

    def CreateWidgets(self):
        frameText = Frame(self, relief=SUNKEN, height=700)
        frameCommands = Frame(self, relief=SUNKEN)
        frameButtons = Frame(self)
        self.buttonOk = Button(frameButtons, text='Close', command=self.Ok, takefocus=FALSE)
        self.scrollbarView = Scrollbar(frameText, orient=VERTICAL, takefocus=FALSE, highlightthickness=0)
        self.textView = Text(frameText, wrap=WORD, highlightthickness=0, fg=self.fg, bg=self.bg, font=self.font, padx=8, pady=8)
        self.scrollbarView.config(command=self.textView.yview)
        self.textView.config(yscrollcommand=self.scrollbarView.set)

        self.commandPrompt = Label(frameCommands, text="> ")
        fontfamilies = tkFont.families()
        if "Consolas" in fontfamilies:
            fixedFont = tkFont.Font(family='Consolas', size=11)
        elif "Lucida Console" in fontfamilies:
            fixedFont = tkFont.Font(family='Lucida Console', size=11)
        elif "DejaVu Sans Mono" in fontfamilies:
            fixedFont = tkFont.Font(family='DejaVu Sans Mono', size=11)
        else:
            fixedFont = tkFont.nametofont('TkFixedFont').copy()
            fixedFont["size"]=11
        self.commandEntry = Entry(frameCommands, takefocus=TRUE, font=fixedFont)
        self.commandEntry.bind('<Return>',self.user_cmd) #dismiss dialog
        self.commandEntry.bind('<F1>', self.f1_pressed)
        self.buttonOk.pack()
        self.scrollbarView.pack(side=RIGHT,fill=Y)
        self.textView.pack(side=LEFT,expand=TRUE,fill=BOTH)
        self.commandPrompt.pack(side=LEFT)
        self.commandEntry.pack(side=LEFT, expand=TRUE, fill=X, ipady=1)

        frameButtons.pack(side=BOTTOM,fill=X)
        frameText.pack(side=TOP,expand=TRUE,fill=BOTH)
        frameCommands.pack(side=BOTTOM, fill=X)
        self.commandEntry.focus_set()

    def f1_pressed(self, e):
        self.commandEntry.delete(0, END)
        self.commandEntry.insert(0, "help")
        self.commandEntry.event_generate("<Return>")

    def user_cmd(self, e):
        cmd = self.commandEntry.get()
        self.textView.config(state=NORMAL)
        self.textView.insert(END, "you typed: %s\n" % cmd)
        self.textView.config(state=DISABLED)
        self.textView.yview(END)
        self.commandEntry.delete(0, END)


    def Ok(self, event=None):
        self.destroy()


def view_text(parent, title, text, modal=True):
    return TextViewer(parent, title, text, modal)


if __name__ == '__main__':
    #test the dialog
    root=Tk()
    root.title('textView test')
    btn1 = Button(root, text='view_text',
        command=lambda:view_text(root, 'view_text', "Tale text window.\n\n"))
    btn1.pack(side=LEFT)
    btn3 = Button(root, text='nonmodal view_text',
        command=lambda:view_text(root, 'nonmodal view_text', "Tale text window\n\n", modal=False))
    btn3.pack(side=LEFT)
    close = Button(root, text='Close', command=root.destroy)
    close.pack(side=RIGHT)
    root.mainloop()
