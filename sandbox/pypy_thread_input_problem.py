# This little test program triggers a bug (?) in Pypy. (versions 1.9 and 2.0-beta1 tested).
# It crashes with a "signal() must be called from the main thread"
# once you enter something at the second input prompt.
# https://bugs.pypy.org/issue1349

import threading, time
import readline   # without readline, no problems

class AsyncInput(threading.Thread):
    def run(self):
        raw_input("(from thread) Type something else: ")

# this input statement triggers the signal bug in pypy at the input in the thread
# removing it makes the problem go away...
raw_input("(from main) Type something: ")

async = AsyncInput()
async.daemon = True
async.start()
time.sleep(100)
