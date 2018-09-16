
import json
import platform
import os
import stat
import tarfile

try:
    from urllib.request import urlretrieve, urlopen
except:
    # Python 2
    from urllib import urlretrieve
    from urlib2 import urlopen

def conda_package_url(name, version=None, label="main"):
    system = platform.system().lower()
    machine = platform.machine()
    with urlopen("http://api.anaconda.org/package/{}".format(name)) as fd:
        data = json.load(fd)
    if version is None:
        version = data["latest_version"]
    b = None
    for f in data["files"]:
        if f["version"] != version:
            continue
        if label not in f["labels"]:
            continue
        if f["attrs"]["operatingsystem"] is not None:
            if f["attrs"]["operatingsystem"] != system:
                continue
            if f["attrs"]["machine"] != machine:
                continue
        if b is None or f["attrs"]["build_number"] > b["attrs"]["build_number"]:
            b = f
    return "http:{}".format(b["download_url"]) if b else None

