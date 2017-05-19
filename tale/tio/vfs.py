"""
Virtual file system.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import os
import io
import sys
import errno
import mimetypes
import pkgutil
import pathlib
from typing import ByteString, Union, IO, Any


__all__ = ["VfsError", "VirtualFileSystem", "internal_resources"]


class VfsError(IOError):
    """Something went wrong while using the virtual file system"""
    pass


class Resource:
    """Simple container of a resource name, its data (string or binary) and the mime type"""
    def __init__(self, name: str, data: Union[str, ByteString], mimetype: str, mtime: float) -> None:
        self.name = name
        self.data = data
        self.mimetype = mimetype
        self.mtime = mtime      # not always set

    def __repr__(self):
        return "<Resource %s from %s, size=%d, mtime=%s>" % (self.mimetype, self.name, len(self.data), self.mtime)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, item: int) -> Union[str, int]:
        return self.data[item]


class VirtualFileSystem:  # @todo convert to using pathlib instead of os.path
    """
    Simple filesystem abstraction. Loads resource files embedded inside a package directory.
    If not readonly, you can write data as well. The API is loosely based on a dict.
    Can be based off an already imported module, or from a file system path somewhere else.
    """
    def __init__(self, root_package: str=None, root_path: Union[str, pathlib.Path]=None, readonly: bool=True) -> None:
        if root_package is not None and root_path is not None:
            raise ValueError("specify only one root argument")
        if not readonly and not root_path:
            raise ValueError("Read-write vfs requires path string")
        self.readonly = readonly
        if root_path:
            self.root = os.path.abspath(os.path.normpath(str(root_path)))
            self.use_pkgutil = False
            if not os.path.isdir(self.root):
                raise VfsError("root path doesn't exist: ", self.root)
            if not os.access(self.root, os.R_OK):
                raise VfsError("no read access: ", self.root)
        else:
            try:
                test = pkgutil.get_data(root_package, "@dummy@")
            except IOError:
                test = b"okay"
            except ImportError:
                test = None
            if test is None:
                raise VfsError("root package cannot be accessed")
            self.root = root_package
            self.use_pkgutil = True

    def validate_path(self, path: str) -> str:
        """
        Validates the given relative path.
        If the vfs is loading from a package, the path is returned unmodified if it is valid.
        If the vfs is loading from a file system location, the absolute path is returned if it is valid.
        """
        if "\\" in path:
            raise VfsError("path must use forward slash '/' as separator, not backward slash '\\'")
        if os.path.isabs(path):
            raise VfsError("path must be relative to the story root folder")
        if self.use_pkgutil:
            return path
        else:
            path = os.path.abspath(os.path.join(self.root, path))
            if not path.startswith(self.root):
                raise VfsError("path must not escape root folder")
            return path

    def __getitem__(self, name: str) -> Resource:
        """Reads the resource data (text or binary) for the given name and returns it as a Resource object"""
        phys_path = self.validate_path(name)
        mimetype = mimetypes.guess_type(name)[0] or ""
        if mimetype.startswith("text/"):
            mode = "rt"
            encoding = "utf-8"
        else:
            mode = "rb"
            encoding = None
        if self.use_pkgutil:
            # package resource access
            # we can't use pkgutil.get_data directly, because we also need the mtime
            # so we do some of the work that get_data does ourselves...
            loader = pkgutil.get_loader(self.root)
            rootmodule = sys.modules[self.root]
            parts = name.split('/')
            parts.insert(0, os.path.dirname(rootmodule.__file__))
            name = os.path.join(*parts)
            mtime = loader.path_stats(name)["mtime"]        # type: ignore
            data = loader.get_data(name)                    # type: ignore
            if encoding:
                with io.StringIO(data.decode(encoding), newline=None) as f_s:
                    return Resource(name, f_s.read(), mimetype, mtime)
            else:
                return Resource(name, data, mimetype, mtime)
        else:
            # direct filesystem access
            with io.open(phys_path, mode=mode, encoding=encoding) as f_b:
                mtime = os.path.getmtime(phys_path)  # os.fstat(f.fileno()).st_mtime
                return Resource(name, f_b.read(), mimetype, mtime)

    def __setitem__(self, name: str, data: Union[Resource, str, ByteString]) -> None:
        """
        Stores the data on the given resource name.
        Overwrites an existing resource if any.
        You can provide a resource object to save, or the data directly (str or bytes).
        """
        if self.readonly:
            raise VfsError("attempt to write a read-only vfs")
        self.validate_path(name)
        if isinstance(data, Resource):
            data = data.data
        with self.open_write(name) as f:
            f.write(data)   # type: ignore

    def __delitem__(self, name: str) -> None:
        """Deletes the given resource"""
        if self.readonly:
            raise VfsError("attempt to write a read-only vfs")
        phys_path = self.validate_path(name)
        try:
            os.remove(phys_path)
        except IOError:
            pass

    def open_write(self, name: str, mimetype: str=None, append: bool=False) -> IO[Any]:
        """returns a writable file io stream"""
        if self.readonly:
            raise VfsError("attempt to write to a read-only vfs")
        phys_path = self.validate_path(name)
        dirname = os.path.dirname(phys_path)
        try:
            if dirname:
                os.makedirs(dirname)    # make sure the path exists
        except OSError as ex:
            if ex.errno != errno.EEXIST or not os.path.isdir(dirname):
                raise
        mimetype = mimetype or mimetypes.guess_type(name)[0] or ""
        if mimetype.startswith("text/"):
            return io.open(phys_path, mode="at" if append else "wt", encoding="utf-8", newline="\n")
        return io.open(phys_path, mode="ab" if append else "wb")


# create a readonly resource loader for Tale's own internal resources:
internal_resources = VirtualFileSystem(root_package="tale")
