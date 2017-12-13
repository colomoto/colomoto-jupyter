
import os
from urllib.parse import urlparse
from urllib.request import urlretrieve

from .sessionfiles import new_output_file
from .ui import info

def download(url, suffix=None):
    filename = new_output_file(suffix=suffix)
    info("Downloading '%s' to '%s'" % (url, filename))
    filename, _ = urlretrieve(url, filename=filename)
    return filename

def ensure_localfile(filename):
    uri = urlparse(filename)
    if uri.netloc:
        bname = os.path.basename(filename)
        filename = download(uri.geturl(), suffix=bname)
    assert os.path.exists(filename)
    return filename

