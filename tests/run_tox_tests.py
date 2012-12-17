import sys
import os
import unittest

def run_tests(args):
    if args:
        if args[0]=="-c":
            os.chdir(args[1])
    if os.path.exists("tale/__init__.py"):
        raise RuntimeError("don't run me from the project root, run me from within the test directory")
    suite = unittest.defaultTestLoader.discover(".")
    unittest.TextTestRunner(verbosity=1).run(suite)


if __name__=="__main__":
    run_tests(sys.argv[1:])
