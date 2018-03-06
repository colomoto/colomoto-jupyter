
import os
import tempfile

from colomoto_jupyter import IN_IPYTHON

CFG = {
    "output_dir": tempfile.gettempdir(),
    "autoclean": True,
}
"""
Python module configuation:

* `output_dir`: directory to use for saving intermediary files.
* `autoclean`: if True, intermediary files will be deleted at script exit
"""

__TMPFILES = []

def preserve_output_files(output_dir="gen"):
    """
    Make intermediate output files in directory `output_dir` instead of default
    system temporary directory, and do not remove them when the script
    terminates.
    """
    CFG["output_dir"] = dest
    CFG["autoclean"] = False

def output_dir():
    """
    Creates the output directory and returns its path
    """
    if not os.path.exists(CFG["output_dir"]):
        os.makedirs(CFG["output_dir"])
    return CFG["output_dir"]


def new_output_file(ext=None, **tempargs):
    """
    Creates a new file in :py:func:`output_dir` using `tempfile.mkstemp
    <https://docs.python.org/3/library/tempfile.html#tempfile.mkstemp>`_ and
    returns its path.
    The parameter `ext` specifies the extension of the file;
    `tempargs` are forwarded to ``tempfile.mkstemp`` with ``prefix=colomoto`` by
    default.
    """
    if "prefix" not in tempargs:
        tempargs["prefix"] = "colomoto"
    if ext is not None:
        tempargs["suffix"] = "%s.%s" % (tempargs.get("suffix", ""), ext)
    fd, filename = tempfile.mkstemp(dir=output_dir(), **tempargs)
    os.close(fd)
    __TMPFILES.append(filename)
    if IN_IPYTHON:
        return os.path.relpath(filename)
    else:
        return os.path.abspath(filename)

def remove_output_files():
    """
    Removes files created by colomoto if `autoclean=True`, and in particular if
    :py:func:`preserve_output_files` has not been called.
    """
    if not CFG["autoclean"]:
        return
    for filename in __TMPFILES:
        if os.path.exists(filename):
            os.unlink(filename)
    __TMPFILES.clear()

import atexit
atexit.register(remove_output_files)

__all__ = [
    "output_dir",
    "new_output_file",
    "remove_output_files",
    "preserve_output_files",
]

