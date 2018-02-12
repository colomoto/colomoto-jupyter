
import os
from urllib.parse import urlparse
from urllib.request import urlretrieve

from .sessionfiles import new_output_file
from .ui import info

import cellcollective

def download(url, suffix=None):
    filename = new_output_file(suffix=suffix)
    info("Downloading '%s'" % url)
    filename, _ = urlretrieve(url, filename=filename)
    return filename

def ensure_localfile(filename):
    uri = urlparse(filename)
    if uri.netloc:
        if cellcollective.url_matches(filename):
            cellc = cellcollective.connect(filename)
            bname = cellc.sbml_basename
            url = cellc.sbml_url
        else:
            bname = os.path.basename(filename)
            url = uri.geturl()
        filename = download(url, suffix=bname)
    assert os.path.exists(filename)
    return filename

