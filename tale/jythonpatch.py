"""
Patch broken stuff in Jython (2.7b1+) to get Tale to work.
Once the official Jython 2.7 has these issues fixed, this
patching code can be removed.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import os
import sys


def jython_patch_2010():
    """add missing timedelta.total_seconds method (http://bugs.jython.org/issue2010)"""
    import datetime
    if hasattr(datetime.timedelta, "total_seconds"):
        return 0

    def total_seconds(td):
        return td.days * 24 * 3600 + td.seconds + td.microseconds / 1000000.0

    datetime.timedelta.total_seconds = total_seconds
    return 1


def jython_patch_1949():
    """fix deque to support maxlen (http://bugs.jython.org/issue1949)"""
    import collections
    try:
        collections.deque("test", 10)
        return 0
    except TypeError:
        class JythonDeque(collections.deque):
            """an inefficient but simple fix for the missing maxlen in Jython's deque type"""
            def __init__(self, iterable=(), maxlen=None):
                super(JythonDeque, self).__init__(iterable)
                self.maxlen = maxlen

            def _truncate_left(self):
                if self.maxlen:
                    while len(self) > self.maxlen:
                        self.popleft()

            def _truncate_right(self):
                if self.maxlen:
                    while len(self) > self.maxlen:
                        self.pop()

            def append(self, item):
                super(JythonDeque, self).append(item)
                self._truncate_left()

            def appendleft(self, item):
                super(JythonDeque, self).appendleft(item)
                self._truncate_right()

            def extend(self, iterable):
                super(JythonDeque, self).extend(iterable)
                self._truncate_left()

            def extendleft(self, iterable):
                super(JythonDeque, self).extendleft(iterable)
                self._truncate_right()

        collections.deque = JythonDeque
        return 1


def jython_patch_2014():
    """patch os.makedirs (http://bugs.jython.org/issue2014)"""
    import errno
    orig_makedirs = os.makedirs

    def makedirs(name, mode=511):     # 511=0777
        try:
            return orig_makedirs(name, mode)
        except OSError as x:
            if x.errno == 20047:
                raise OSError(errno.EEXIST, "can't create a path that already exists")
            raise

    os.makedirs = makedirs
    return 1


if os.name == "java":
    if sys.version_info < (2, 7):
        raise RuntimeError("Tale requires at least Jython 2.7b1 to run on Jython")
    num_patches = jython_patch_2010() + jython_patch_1949() + jython_patch_2014()
    if num_patches > 0:
        import warnings
        warnings.warn("patched jython to fix some broken stuff", RuntimeWarning)
