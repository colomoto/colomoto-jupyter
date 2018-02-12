
import re

from urllib.parse import urlparse

from xml.dom import *
from xml.dom.minidom import parse

from bs4 import BeautifulSoup

from colomoto_jupyter import *

if IN_IPYTHON:
    from IPython.display import Markdown

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

class CellCollectiveConnector(object):
    def __init__(self, identifier):
        self.id = id_from_url(identifier) or identifier
    @property
    def sbml_url(self):
        return "http://api.cellcollective.org/model/export/{}?type=SBML".format(self.id)
    @property
    def sbml_basename(self):
        return "{}.sbml".format(self.id)

def connect(identifier):
    return CellCollectiveConnector(identifier)


METADATA_UNITPROTID = "UniProtID"
METADATA_GENENAME = "GeneName"
METADATA_NCBIGENEID = "NCBIGeneID"

QUALNS = "http://www.sbml.org/sbml/level3/version1/qual/version1"

class CellCollectiveSBMLModel(object):
    def __init__(self, localfile):
        self.localfile = localfile
        self.dom = parse(localfile)
        self.root = self.dom.documentElement
        species_elts = self.root.getElementsByTagNameNS(QUALNS, "qualitativeSpecies")
        self.id2elt = dict([(e.getAttributeNS(QUALNS, "id"), e) \
                                for e in species_elts])
        self.name2id = dict([(e.getAttributeNS(QUALNS, "name"), id) \
                                for id, e in self.id2elt.items()])

    @property
    def species(self):
        """
        Returns the set of defined species

        :rtype: set
        """
        return set(self.name2id.keys())

    _key2metadata = {
        "uniprotid": METADATA_UNITPROTID,
        "uniprotaccessionid": METADATA_UNITPROTID,
        "genename": METADATA_GENENAME,
        "ncbigeneid": METADATA_NCBIGENEID,
    }

    def species_metadata(self, name):
        metadata = {}
        notes = self.id2elt[self.name2id[name]].getElementsByTagName("notes")
        bodies = notes[0].getElementsByTagName("body") if notes else None
        ps = bodies[0].getElementsByTagName("p") if bodies else None
        if not ps:
            return metadata
        htmldata = BeautifulSoup(ps[0].firstChild.wholeText, "html.parser")
        divs = htmldata.find_all("div")
        for div in divs:
            t = div.getText().split(":")
            if len(t) == 2:
                key = t[0].strip().replace(" ","").lower()
                value = t[1].strip()
                if key in self._key2metadata:
                    metadata[self._key2metadata[key]] = value
        return metadata

    def species_uniprotkb(self, name):
        uniprotid = self.species_metadata(name).get(METADATA_UNITPROTID)
        if not uniprotid:
            return
        return URL("https://www.uniprot.org/uniprot/%s" % uniprotid)

    def species_ncbi_gene(self, name):
        id = self.species_metadata(name).get(METADATA_NCBIGENEID)
        if not id:
            return
        return URL("https://www.ncbi.nlm.nih.gov/gene/%s" % id)



def load(identifier):
    conn = None
    if isinstance(identifier, CellCollectiveConnector):
        conn = identifier
    elif url_matches(identifier):
        conn = CellCollectiveConnector(identifier)
    else:
        sbmlfile = identifier
    if conn:
        from colomoto_jupyter.io import download
        url = conn.sbml_url
        bname = conn.sbml_basename
        sbmlfile = download(url, suffix=bname)
    return CellCollectiveSBMLModel(sbmlfile)

def to_biolqm(model):
    biolqm = import_colomoto_tool("biolqm")
    return biolqm.load(model.localfile)

