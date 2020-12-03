
import os
import shutil
from urllib.parse import urlparse
from urllib.request import urlretrieve

from .sessionfiles import new_output_file
from .ui import info, logger

from colomoto_jupyter import IN_IPYTHON
import colomoto_jupyter.config as cfg

if IN_IPYTHON:
    from IPython.display import display, FileLink

import cellcollective

def download(url, suffix=None):
    filename = new_output_file(suffix=suffix)
    info("Downloading %s" % url)
    filename, _ = urlretrieve(url, filename=filename)
    return filename

def auto_download(url, dest):
    if cfg.auto_persistent and os.path.isfile(dest):
        if IN_IPYTHON:
            display(FileLink(dest, result_html_prefix="Using local file "))
            return dest
    filename = download(url, suffix=dest)
    if cfg.auto_persistent:
        shutil.move(filename, dest)
        filename = dest
        if IN_IPYTHON:
            logger.warning(f"Do not forget attaching \"{dest}\" file with your notebook")
            display(FileLink(dest, result_html_prefix="Using local file "))
    return filename

def ensure_localfile(filename):
    uri = urlparse(filename)
    if uri.netloc:
        if cellcollective.url_matches(filename):
            return cellcollective.load(filename,
                    auto_persistent=cfg.auto_persistent).localfile
        bname = os.path.basename(uri.path)
        url = uri.geturl()
        filename = auto_download(url, bname)
    assert os.path.exists(filename)
    return filename
