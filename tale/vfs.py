"""
Virtual file system.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import errno
import io
import mimetypes
import os
import pathlib
import pkgutil
import sys
from typing import ByteString, Union, IO, Any, Iterable

__all__ = ["VfsError", "VirtualFileSystem", "internal_resources"]

if ".7z" not in mimetypes.encodings_map:
    mimetypes.encodings_map[".7z"] = "7zip"
if ".rar" not in mimetypes.encodings_map:
    mimetypes.encodings_map[".7z"] = "rar"
if ".json" not in mimetypes.types_map:
    mimetypes.types_map[".json"] = "application/json"
if ".ini" not in mimetypes.types_map:
    mimetypes.types_map[".ini"] = "text/plain"


class VfsError(IOError):
    """Something went wrong while using the virtual file system"""
    pass


def is_text(mimetype: str) -> bool:
    return bool(mimetype) and (mimetype.startswith("text/") or mimetype in {"application/json", "application/xml"})


class Resource:
    """Simple container of a resource name, its data (string or binary) and the mime type"""
    def __init__(self, name: str, data: Union[str, ByteString], mimetype: str="application/octet-stream", mtime: float=0.0) -> None:
        self.is_text = is_text(mimetype)
        if self.is_text:
            if not isinstance(data, str):
                raise TypeError("text data required for this mimetype")
        else:
            if not isinstance(data, (bytes, bytearray)):
                raise TypeError("bytes or bytearray data requires for this mimetype")
        self.name = name
        self.mimetype = mimetype
        self.mtime = mtime
        self.__data = data

    @property
    def data(self) -> bytes:
        """the (binary) data of this resource"""
        if self.is_text:
            raise VfsError("this is a text resource, not binary")
        return self.__data      # type: ignore

    @property
    def text(self) -> str:
        """the (text) data of this resource"""
        if self.is_text:
            return self.__data   # type: ignore
        raise VfsError("this is a binary resource, not text")

    def __repr__(self):
        return "<Resource %s from %s, size=%d, mtime=%s, is_text=%s>" \
               % (self.mimetype, self.name, len(self.__data), self.mtime, self.is_text)

    def __len__(self) -> int:
        return len(self.__data)

    def __getitem__(self, item: int) -> Union[str, int]:
        return self.__data[item]


class VirtualFileSystem:
    """
    Simple filesystem abstraction. Loads resource files embedded inside a package directory.
    If not readonly, you can write data as well. The API is loosely based on a dict.
    Can be based off an already imported module, or from a file system path somewhere else.
    If dealing with text files, the encoding is always UTF-8.
    It supports automatic decompression of .gz, .xz and .bz2 compressed files (as long as they have that extension).
    It automatically returns the contents of a compressed version of a requested file if the file
    itself doesn't exist but there is a compressed version of it available.
    """
    def __init__(self, root_package: str=None, root_path: Union[str, pathlib.Path]=None,
                 readonly: bool=True, everythingtext: bool=False) -> None:
        if root_package is not None and root_path is not None:
            raise ValueError("specify only one root argument")
        if not readonly and not root_path:
            raise ValueError("Read-write vfs requires root_path argument")
        self.readonly = readonly
        self.everythingtext = everythingtext
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
        original_name = name
        phys_path = self.validate_path(name)
        mimetype, compressor = mimetypes.guess_type(name, False)
        mimetype = mimetype or "application/octet-stream"
        if self.everythingtext:
            mimetype = "text/plain"
        encoding = None
        mode = "rb"
        if not compressor and is_text(mimetype):
            mode = "rt"     # normalized line endings
            encoding = "utf-8"
        if self.use_pkgutil:
            # package resource access
            # we can't use pkgutil.get_data directly, because we also need the mtime
            # so we do some of the work that get_data does ourselves...
            loader = pkgutil.get_loader(self.root)
            rootmodule = sys.modules[self.root]
            parts = name.split('/')
            parts.insert(0, os.path.dirname(rootmodule.__file__))
            name = os.path.join(*parts)
            try:
                data = loader.get_data(name)    # type: ignore
                if not data:
                    raise FileNotFoundError(errno.ENOENT, name)
            except FileNotFoundError as x:
                # if the file cannot be found directly, attempt to read a compressed version of it
                for suffix in mimetypes.encodings_map:
                    try:
                        data = loader.get_data(name + suffix)    # type: ignore
                        if data:
                            return self[original_name + suffix]
                    except FileNotFoundError:
                        pass
                raise x
            else:
                data = loader.get_data(name)   # type: ignore
                if not data:
                    raise FileNotFoundError(errno.ENOENT, name)
            try:
                mtime = loader.path_stats(name)["mtime"]        # type: ignore
            except AttributeError:
                mtime = 0.0   # not all loaders support getting the modification time...
            if encoding:
                with io.StringIO(data.decode(encoding), newline=None) as f_s:
                    return Resource(name, f_s.read(), mimetype, mtime)
            else:
                if compressor:
                    data = self._uncompress(compressor, data, is_text(mimetype))
                return Resource(name, data, mimetype, mtime)
        else:
            # direct filesystem access
            if not os.path.isfile(phys_path):
                # if the file cannot be found directly, attempt to read a compressed version of it
                for suffix in mimetypes.encodings_map:
                    if os.path.exists(phys_path + suffix):
                        return self[original_name + suffix]
            with io.open(phys_path, mode=mode, encoding=encoding) as f_b:
                mtime = os.path.getmtime(phys_path)
                data = f_b.read()
                if compressor:
                    assert not encoding, "compressed data should not have encoding"
                    data = self._uncompress(compressor, data, is_text(mimetype))
                return Resource(name, data, mimetype, mtime)

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
            f.write(data)

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
        if is_text(mimetype):
            return io.open(phys_path, mode="at" if append else "wt", encoding="utf-8", newline="\n")
        return io.open(phys_path, mode="ab" if append else "wb")

    def contents(self, path: str=".") -> Iterable[str]:
        """Returns the files in the given path. Only works on path based vfs, not for package based vfs."""
        if self.use_pkgutil:
            raise VfsError("cannot list the contents of a package based vfs")
        phys_path = self.validate_path(path)
        return [name for name in os.listdir(phys_path) if os.path.isfile(os.path.join(phys_path, name))]

    def _uncompress(self, compressor: str, data: bytes, expect_text: bool) -> Union[bytes, str]:
        if compressor == "bzip2":
            import bz2
            data = bz2.decompress(data)
        elif compressor == "xz":
            import lzma
            data = lzma.decompress(data)
        elif compressor == "gzip":
            import gzip
            data = gzip.decompress(data)
        else:
            raise VfsError("unsupported compressor: " + compressor)
        if expect_text:
            # convert to utf-8 text with normalized line endings
            text = data.decode("utf-8")
            last_lf = text.endswith(('\r', '\n'))
            text = "\n".join(text.splitlines())
            if last_lf:
                text += "\n"
            return text
        return data


# create a readonly resource loader for Tale's own internal resources:
internal_resources = VirtualFileSystem(root_package="tale")
