"""
The actual mudlib 'world' code

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

# this is intentionally left empty; don't put stuff here that other modules
# might need, it's too easy to cause circular dependencies

__version__ = "1.4"

from . import jythonpatch   # patch some stuff in jython, if needed

class _MudContext(object):
    pass

mud_context = _MudContext()

