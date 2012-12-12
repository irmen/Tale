"""
An attempt to reproduce the following Pypy problem:   (unsuccesful so far)

BUG: on pypy when using readline (linux/osx), and async input thread (servermode=timer),
     driver.input crashes with:  signal.signal(signal.SIGWINCH, self.old_sigwinch)
                                ValueError: signal() must be called from the main thread

"""
from __future__ import print_function
import time
from tale.io.console_io import ConsoleIo
import readline
readline.parse_and_bind("tab: complete")


class Player(object):
    def store_input_line(self, cmd):
        print("you entered: ", cmd)


if __name__=="__main__":
    io = ConsoleIo()
    player = Player()
    player.io = io
    ainput = io.get_async_input(player)
    print("[main] running")
    while True:
        ainput.enable()
        time.sleep(1)
    print("[main] exiting")

