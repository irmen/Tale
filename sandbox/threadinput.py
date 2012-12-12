from __future__ import print_function
import threading
import sys
import time
import readline

readline.parse_and_bind("tab: complete")

if sys.version_info < (3,0):
    input = raw_input

class InputThread(threading.Thread):
    def __init__(self):
        super(InputThread, self).__init__()
        self.daemon = True
        self.enabled = threading.Event()
        self.start()

    def run(self):
        while True:
            self.enabled.wait()
            string = input("[thread] enter something: ")
            print("[thread] you entered:", string)
            self.enabled.clear()


if __name__=="__main__":
    it = InputThread()
    print("[main] running")
    it.enabled.set()
    time.sleep(100)
