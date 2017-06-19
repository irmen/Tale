"""
The actual mudlib 'world' code

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import sys
from distutils.version import LooseVersion
from typing import Any


__version__ = "3.4"


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


def _check_required_libraries():
    try:
        import appdirs
    except ImportError:
        appdirs = None
    try:
        import colorama
    except ImportError:
        colorama = None
    try:
        import smartypants
    except ImportError:
        smartypants = None
    try:
        import serpent
    except ImportError:
        serpent = None
    all_good = True
    smartypants_version_required = LooseVersion("1.8.6")
    colorama_version_required = LooseVersion("0.3.6")
    serpent_version_required = LooseVersion("1.22")
    if not appdirs:
        print("The 'appdirs' Python library (any recent version) is required to play this game.", file=sys.stderr)
        all_good = False
    if not colorama or LooseVersion(colorama.__version__) < colorama_version_required:
        print("The 'colorama' Python library (version >= {}) is required to play this game."
              .format(colorama_version_required), file=sys.stderr)
        all_good = False
    if not smartypants or LooseVersion(smartypants.__version__) < smartypants_version_required:
        print("The 'smartypants' Python library (version >= {}) is required to play this game."
              .format(smartypants_version_required), file=sys.stderr)
        all_good = False
    if not serpent or LooseVersion(serpent.__version__) < serpent_version_required:
        print("The 'serpent' Python library (version >= {}) is required to play this game."
              .format(serpent_version_required), file=sys.stderr)
        all_good = False
    if not all_good:
        print("\nInstall this/these and try again. Try using your package manager (on Linux) or try executing the following command:")
        print('  pip install --user "appdirs" "smartypants>={spv}" "colorama>={cv}" "serpent>={sv}"'
              .format(spv=smartypants_version_required, cv=colorama_version_required, sv=serpent_version_required))
        input("\nEnter to exit: ")
        raise SystemExit(1)

_check_required_libraries()
del _check_required_libraries
