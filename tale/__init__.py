"""
The actual mudlib 'world' code

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from typing import Any


__version__ = "3.2"


class _MudContext:
    driver = None      # type: Any
    config = None      # type: Any
    resources = None   # type: Any


# The mud_context is a global container for the following attributes,
# that will be set (by the driver) to the correct initialized instances:
#  - driver   (driver)
#  - config   (story config)
#  - resources  (story's file resources, just a shortcut to driver.resources)
mud_context = _MudContext()
