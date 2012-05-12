from socket import *

class Living(object):
    def __init__(self, name):
        self.name=name
        self.buffer=[]

    def input_loop(self):
        while True:
            message, userinput = yield self.buffer
            if userinput=="stop":
                break
            if message:
                print("[%s] got msg: %s" % (self.name, message))
            if userinput:
                self.buffer.append("[%s] userinput was: %s" % (self.name, userinput))



def main():
    l1 = Living("eric")
    l2 = Living("suzy")


    e1 = l1.input_loop()
    e1.next()

    buffer = e1.send(("message1", None))
    print buffer


if __name__ == "__main__":
    main()
