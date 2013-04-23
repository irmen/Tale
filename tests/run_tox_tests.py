import sys
import os
import unittest


def run_tests(args):
    if args:
        if args[0]=="-c":
            os.chdir(args[1])
    suite = unittest.defaultTestLoader.discover(".")
    unittest.TextTestRunner(verbosity=1).run(suite)


if __name__=="__main__":
    run_tests(sys.argv[1:])
