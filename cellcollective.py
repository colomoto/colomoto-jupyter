
import re

from urllib.parse import urlparse

urlidentifier = re.compile("https?://[^/]*\\bcellcollective\.org/#(\\d+)\\b")

def id_from_url(url):
    uri = urlparse(url)
    if uri.netloc:
        if uri.scheme == "cellcollective":
            return uri.netloc
        urlmatch = urlidentifier.search(url)
        if urlmatch:
            return urlmatch.group(1)

def url_matches(url):
    return id_from_url(url) is not None

class CellCollectiveModel(object):
    def __init__(self, identifier):
        self.id = id_from_url(identifier) or identifier
    @property
    def sbml_url(self):
        return "http://api.cellcollective.org/model/export/{}?type=SBML".format(self.id)
    @property
    def sbml_basename(self):
        return "{}.sbml".format(self.id)


def connect(identifier):
    return CellCollectiveModel(identifier)

