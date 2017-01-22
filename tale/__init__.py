# coding=utf-8
"""
The actual mudlib 'world' code

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

# this is intentionally left empty; don't put stuff here that other modules
# might need, it's too easy to cause circular dependencies

__version__ = "2.8"


class _MudContext(object):
    pass


# The mud_context is a global container for the following attributes,
# that will be set (by the driver) to the correct initialized instances:
#  - driver   (driver)
#  - config   (story config)
mud_context = _MudContext()
