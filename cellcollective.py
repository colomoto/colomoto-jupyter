
import re

urlidentifier = re.compile("https?://[^/]*\\bcellcollective\.org/#(\\d+)\\b")

def url_matches(url):
    return urlidentifier.search(url) is not None

def id_from_url(url):
    urlmatch = urlidentifier.search(url)
    if urlmatch:
        return urlmatch.group(1)

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

