"""
Resource loader.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import print_function, division, unicode_literals
import os
import inspect


class ResourceLoader(object):
    """Simple abstraction to load resource files embedded inside a package directory"""
    def __init__(self, root_module_or_path):
        try:
            self.root_path = os.path.dirname(inspect.getabsfile(root_module_or_path))
        except TypeError:
            self.root_path = root_module_or_path

    def open(self, path, mode="r"):
        if "\\" in path:
            raise ValueError("resource paths use forward slash '/' as separator, not backward slash '\\'")
        if os.path.isabs(path):
            raise ValueError("resource paths may not be absolute")
        path = os.path.join(*path.split("/"))   # convert to platform path separator
        path = os.path.join(self.root_path, path)
        return open(path, mode=mode)

    def load_text(self, path):
        with self.open(path, mode="U") as f:
            return f.read()

    def load_image(self, path):
        with self.open(path, mode="rb") as f:
            return f.read()


# create the resource loader for Tale itself:
loader = ResourceLoader(ResourceLoader)
