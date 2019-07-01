import os
import pathlib
import tempfile
from os.path import abspath, dirname, join, normcase, sep

from django.core.exceptions import SuspiciousFileOperation

# For backwards-compatibility in Django 2.0
abspathu = abspath


def upath(path):
    """Always return a unicode path (did something for Python 2)."""
    return path


def npath(path):
    """
    Always return a native path, that is unicode on Python 3 and bytestring on
    Python 2. Noop for Python 3.
    """
    return path


def fspath(path):
    """
    Equivalent of os.fspath in Python 3.7

    Return the path representation of a path-like object.
    If str or bytes is passed in, it is returned unchanged. Otherwise we
    look for a pathlib.Path object or an object with ``__fspath__``
    If the provided path is not str, bytes, Path-like, raise TypeError.
    """
    if isinstance(path, (str, bytes)):
        return path

    # Work from the object's type to match method resolution of other magic
    # methods.
    path_type = type(path)
    if isinstance(path_type, pathlib.Path):
        return str(path_type)
    try:
        path_string = path_type.__fspath__(path)
    except AttributeError:
        if hasattr(path_type, '__fspath__'):
            raise
        else:
            raise TypeError(
                'expected str, bytes or path-like object, not {}'.format(
                path_type.__name__))
    if not isinstance(path_string, (str, bytes)):
        raise TypeError(
            'expected {}.__fspath__() to return str or bytes, '
            'not {}'.format(path_type.__name__, type(path_string).__name__))
    return path_string


def safe_join(base, *paths):
    """
    Join one or more path components to the base path component intelligently.
    Return a normalized, absolute version of the final path.

    Raise ValueError if the final path isn't located inside of the base path
    component.
    """
    final_path = abspath(join(base, *paths))
    base_path = abspath(base)
    # Ensure final_path starts with base_path (using normcase to ensure we
    # don't false-negative on case insensitive operating systems like Windows),
    # further, one of the following conditions must be true:
    #  a) The next character is the path separator (to prevent conditions like
    #     safe_join("/dir", "/../d"))
    #  b) The final path must be the same as the base path.
    #  c) The base path must be the most root path (meaning either "/" or "C:\\")
    if (not normcase(final_path).startswith(normcase(base_path + sep)) and
            normcase(final_path) != normcase(base_path) and
            dirname(normcase(base_path)) != normcase(base_path)):
        raise SuspiciousFileOperation(
            'The joined path ({}) is located outside of the base path '
            'component ({})'.format(final_path, base_path))
    return final_path


def symlinks_supported():
    """
    Return whether or not creating symlinks are supported in the host platform
    and/or if they are allowed to be created (e.g. on Windows it requires admin
    permissions).
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        original_path = os.path.join(temp_dir, 'original')
        symlink_path = os.path.join(temp_dir, 'symlink')
        os.makedirs(original_path)
        try:
            os.symlink(original_path, symlink_path)
            supported = True
        except (OSError, NotImplementedError):
            supported = False
        return supported
