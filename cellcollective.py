
import os
import re

import logging

from urllib.parse import urlparse
from urllib.request import HTTPError

from xml.dom import *
from xml.dom.minidom import parse

from bs4 import BeautifulSoup

from colomoto_jupyter import *

logger = logging.getLogger(__name__)

urlidentifier = re.compile("https?://[^/]*\\bcellcollective\\.org/[^/]*#(\\d+)(:(\\d+))?\\b")

def id_from_url(url):
    uri = urlparse(url)
    if uri.netloc:
        if uri.scheme == "cellcollective":
            identifier = uri.netloc
            if ":" in identifier:
                return tuple(identifier.split(":"))
            else:
                return identifier, 1
        url = url.replace("module/", "")
        urlmatch = urlidentifier.search(url)
        if urlmatch:
            return urlmatch.group(1),\
                    urlmatch.group(3) or 1

def url_matches(url):
    return id_from_url(url) is not None

class CellCollectiveConnector(object):
    def __init__(self, identifier, version=1):
        idv = id_from_url(identifier) or identifier
        if type(idv) is not tuple:
            idv = idv, version
        self.id, self.version = idv
    @property
    def sbml_urls(self):
        url = f"https://research.cellcollective.org/web/api/model/{self.id}/export/version/{self.version}?type=SBML&modeltype=boolean"
        return [url]
    @property
    def sbml_basename(self):
        return f"cellcollective-{self.id}-{self.version}.sbml"

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
        self.id2elt = dict([(e.getAttributeNS(QUALNS, "id"), e)
                                for e in species_elts])
        self.name2id = dict([(e.getAttributeNS(QUALNS, "name"), id)
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

        def parse_statement(data):
            t = data.split(":")
            if len(t) == 2:
                key = t[0].strip().replace(" ","").lower()
                value = t[1].strip()
                if key in self._key2metadata:
                    metadata[self._key2metadata[key]] = value

        divs = htmldata.find_all("div")
        for div in divs:
            parse_statement(div.getText())
        if not divs:
            for p in ps:
                parse_statement(p.firstChild.wholeText)

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



def load(identifier, auto_persistent=True):
    """
    Load a CellCollective model from its URL or SBML export.

    `identifier` can be:
    - a URL of the form ``"cellcollective://{model_id}:{model_version}"``
    - the model URL from `research.cellcollective.org`
    - the location of the SBML file exported from CellCollective

    Whenever `identifier` is one of the two first cases, the module relies on
    the online API of CellCollective to download the SBML file.
    As the API may change over time, it is strongly recommended to rely on
    instead on downloaded SBML files and attach them with the notebook to ensure
    its repeatibility over time.

    With the option ``auto_persistent=True``, the module first looks for an
    existing downloaded SBML file. If it does not exists, it uses the online
    API to download it and move it alongside the notebook.
    """
    conn = None
    if isinstance(identifier, CellCollectiveConnector):
        conn = identifier
    elif url_matches(identifier):
        conn = CellCollectiveConnector(identifier)
    else:
        from colomoto_jupyter.io import ensure_localfile
        sbmlfile = ensure_localfile(identifier)
    if conn:
        from colomoto_jupyter.io import auto_download
        urls = conn.sbml_urls
        bname = conn.sbml_basename
        if not os.path.isfile(bname) and not auto_persistent:
            logger.warning(f"""This command relies on the online CellCollective API which may change over time!
To improve the repeatibility of this notebook, consider using the command

    cellcollective.load("{identifier}", auto_persistent=True)

and attach the "{bname}" file along with your notebook.""")
        for i, url in enumerate(urls):
            try:
                sbmlfile = auto_download(url, bname)
                break
            except HTTPError:
                if i == len(urls)-1:
                    raise
    return CellCollectiveSBMLModel(sbmlfile)

def to_biolqm(model):
    biolqm = import_colomoto_tool("biolqm")
    lqm = biolqm.load(model.localfile)
    return biolqm.sanitize(lqm)
