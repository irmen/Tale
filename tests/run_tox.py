import sys
import os
import unittest


def run_tests(args):
    if args:
        if args[0] == "-c":
            print("CHANGEDIR TO", args[1])
            os.chdir(args[1])
            print("CURDIR:",os.getcwd())
            sys.path.insert(0, ".")
    suite = unittest.defaultTestLoader.discover(".")
    test_results = unittest.TextTestRunner(verbosity=1).run(suite)
    return len(test_results.errors) + len(test_results.failures)


if __name__ == "__main__":
    exit(run_tests(sys.argv[1:]))
