"""
Patch missing stuff in Jython to get Tale to work

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import os

if os.name=="java":
    # fix some missing things in Jython 2.7
    import datetime
    patched = False
    if not hasattr(datetime.timedelta, "total_seconds"):
        # add missing timedelta.total_seconds method (issue 2010)
        def total_seconds(td):
            return td.days*24*3600+td.seconds+td.microseconds/1000000.0
        datetime.timedelta.total_seconds = total_seconds
        t=datetime.timedelta(1, 45, 123456)
        assert t.total_seconds()==86445.123456
        patched = True
    import collections
    try:
        d = collections.deque("test", 10)
    except TypeError:
        # fix deque to support maxlen (issue 1949)
        orig_deque = collections.deque
        class JythonDeque(orig_deque):
            def __init__(self, iterable=(), maxlen=None):
                orig_deque.__init__(self, iterable)
                # skip the maxlen thing altogether for now
        collections.deque = JythonDeque
        patched = True
    # patch os.makedirs (issue 2014)
    import errno
    orig_makedirs = os.makedirs
    def makedirs(name, mode=511):     # 511=0777
        try:
            return orig_makedirs(name, mode)
        except OSError as x:
            if x.errno==20047:
                raise OSError(errno.EEXIST, "can't create a path that already exists")
            raise
    os.makedirs = makedirs
    patched = True
    if patched:
        import warnings
        warnings.warn("patched jython to fix some broken stuff", RuntimeWarning)
