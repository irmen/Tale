"""
Virtual file system.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import os
import errno
import inspect
try:
    from appdirs import user_data_dir
except ImportError:
    # for platforms lacking this module, we have a workaround
    def user_data_dir(appname, appauthor=None, version=None, roaming=False):
        return os.path.join(os.path.expanduser("~"), appname + "-data")


class VfsError(IOError):
    pass


class VirtualFileSystem(object):
    """
    Simple filesystem abstraction.
    loads resource files embedded inside a package directory.
    Saves data files to the platform-defined user data directory.
    """
    def __init__(self, root_module_or_path):
        try:
            self.root_path = os.path.dirname(inspect.getabsfile(root_module_or_path))
        except TypeError:
            self.root_path = root_module_or_path

    def validate_path(self, path):
        if "\\" in path:
            raise VfsError("path must use forward slash '/' as separator, not backward slash '\\'")
        if os.path.isabs(path):
            raise VfsError("path may not be absolute")

    def open_read(self, path, mode="r"):
        self.validate_path(path)
        path = os.path.join(*path.split("/"))   # convert to platform path separator
        path = os.path.join(self.root_path, path)
        return open(path, mode=mode)

    def get_userdata_dir(self, path):
        user_data = user_data_dir("Tale", "Razorvine")
        path = os.path.join(user_data, path)
        return path

    def makedirs(self, path):
        directory = os.path.dirname(path)
        try:
            os.makedirs(directory)    # make sure the path exists
        except OSError as ex:
            if ex.errno == errno.EEXIST and os.path.isdir(directory):
                pass
            else:
                raise

    def open_write(self, path, mode="w"):
        self.validate_path(path)
        path = os.path.join(*path.split("/"))   # convert to platform path separator
        path = self.get_userdata_dir(path)
        self.makedirs(path)
        return open(path, mode=mode)

    def load_text(self, path):
        with self.open_read(path, mode="U") as f:
            return f.read()

    def load_image(self, path):
        with self.open_read(path, mode="rb") as f:
            return f.read()

    def load_from_storage(self, path):
        self.validate_path(path)
        path = os.path.join(*path.split("/"))   # convert to platform path separator
        path = self.get_userdata_dir(path)
        with open(path, "rb") as f:
            return f.read()

    def write_to_storage(self, path, data):
        with self.open_write(path, mode="wb") as f:
            f.write(data)

    def delete_storage(self, path):
        self.validate_path(path)
        path = self.get_userdata_dir(path)
        os.remove(path)


# create the resource loader for Tale itself:
from .. import errors   # get a package residing in the Tale package root
vfs = VirtualFileSystem(errors)
