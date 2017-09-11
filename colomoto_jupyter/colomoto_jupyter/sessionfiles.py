
import os
import tempfile

from colomoto_jupyter import IN_IPYTHON

CFG = {
    "output_dir": "gen" if IN_IPYTHON else tempfile.gettempdir(),
}
"""
Python module configuation:

* `output_dir`: directory to use for saving intermediary files.
"""

__TMPFILES = []

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
    _, filename = tempfile.mkstemp(dir=output_dir(), **tempargs)
    __TMPFILES.append(filename)
    return os.path.relpath(filename)

def remove_output_files():
    """
    Removes files created by colomoto
    """
    for filename in __TMPFILES:
        if os.path.exists(filename):
            os.unlink(filename)
    __TMPFILES.clear()

__all__ = [
    "output_dir",
    "new_output_file",
    "remove_output_files",
]

