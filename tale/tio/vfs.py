"""
Virtual file system.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import os
import io
import time
import errno
import inspect
import mimetypes

__all__ = ["VfsError", "VirtualFileSystem", "internal_resources", "userdata"]


class VfsError(IOError):
    pass


class Resource(object):
    """Simple container of a resource name, its data (string or binary) and some bits of metadata"""
    def __init__(self, name, data, mimetype, mtime):
        self.name = name
        self.data = data
        self.mimetype = mimetype
        self.mtime = mtime

    def __repr__(self):
        return "<Resource %s from %s, size=%d>" % (self.mimetype, self.name, len(self.data))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        return self.data[item]


class VirtualFileSystem(object):
    """
    Simple filesystem abstraction.
    Loads resource files embedded inside a package directory.
    If not readonly, you can write data as well.
    """
    def __init__(self, root_module_or_path, readonly=True):
        self.readonly = readonly
        if inspect.ismodule(root_module_or_path):
            if not readonly:
                raise TypeError("Read-write vfs requires explicit path string")
            self.root_path = os.path.dirname(inspect.getabsfile(root_module_or_path))
        else:
            self.root_path = os.path.normpath(root_module_or_path)
        if not os.path.isdir(self.root_path):
            raise VfsError("root path doesn't exist")
        if not os.access(self.root_path, os.R_OK):
            raise VfsError("no read access")

    @staticmethod
    def __validate_path(path):
        if "\\" in path:
            raise VfsError("path must use forward slash '/' as separator, not backward slash '\\'")
        if os.path.isabs(path):
            raise VfsError("path must be relative to the story root folder")

    def __getitem__(self, name):
        """Reads the resource data (text or binary) for the given name and returns it as a Resource object"""
        self.__validate_path(name)
        mimetype = mimetypes.guess_type(name)[0] or ""
        if mimetype.startswith("text/"):
            mode = "rt"
            encoding = "utf-8"
        else:
            mode = "rb"
            encoding = None
        phys_path = os.path.normpath(os.path.join(self.root_path, name))
        with io.open(phys_path, mode=mode, encoding=encoding) as f:
            mtime = os.fstat(f.fileno()).st_mtime
            mtime = time.asctime(time.localtime(mtime))
            return Resource(name, f.read(), mimetype, mtime)

    def open_write(self, name, append=False):
        """returns a writable file io stream"""
        if self.readonly:
            raise VfsError("attempt to write to a read-only vfs")
        self.__validate_path(name)
        phys_path = os.path.normpath(os.path.join(self.root_path, name))
        dirname = os.path.dirname(phys_path)
        try:
            if dirname:
                os.makedirs(dirname)    # make sure the path exists
        except OSError as ex:
            if ex.errno != errno.EEXIST or not os.path.isdir(dirname):
                raise
        mimetype = mimetypes.guess_type(name)[0] or ""
        if mimetype.startswith("text/"):
            return io.open(phys_path, mode="at" if append else "wt", encoding="utf-8", newline="\n")
        return io.open(phys_path, mode="ab" if append else "wb")

    def write(self, name, data):
        """Stores the data on the given resource name. Overwrites an existing resource if any."""
        if self.readonly:
            raise VfsError("attempt to write a read-only vfs")
        self.__validate_path(name)
        with self.open_write(name) as f:
            f.write(data)


# create a readonly resource loader for Tale's own internal resources:
internal_resources = VirtualFileSystem(os.path.join(os.path.dirname(__file__), os.path.pardir))
