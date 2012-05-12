from Tkinter import *

class mywidgets:
    def __init__(self, root):
        frame = Frame(root)
        frame.pack()
        self.txtfr(frame)
        return

    def txtfr(self, frame):
        #define a new frame and put a text area in it
        textfr = Frame(frame)
        self.text = Text(textfr, height=10, width=50, background='white')

        # put a scroll bar in the frame
        scroll = Scrollbar(textfr)
        self.text.configure(yscrollcommand=scroll.set)

        #pack everything
        self.text.pack(side=LEFT)
        scroll.pack(side=RIGHT, fill=Y)
        textfr.pack(side=TOP)
        return


def main():
    root = Tk()
    s = mywidgets(root)
    root.title('textarea')
    root.mainloop()

main()

