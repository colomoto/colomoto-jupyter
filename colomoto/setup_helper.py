
import json
import platform
import os
import shutil
import sys
import tarfile

try:
    from urllib.request import urlretrieve, urlopen
except:
    # Python 2
    from urllib import urlretrieve
    from urllib2 import urlopen

##
# Setup PATH env for custom colomoto installations
#
if platform.system() == "Windows":
    PREFIXES = [os.getenv("APPDATA"), "colomoto"]
    binpaths = [os.path.join(p,"bin") for p in PREFIXES] \
                + [os.path.join(p,"Library","bin") for p in PREFIXES]
else:
    PREFIXES = ["/usr/local/share/colomoto",
        os.path.join(os.path.expanduser("~"), ".local", "share", "colomoto")]
    binpaths = [os.path.join(p, "bin") for p in PREFIXES]

binpaths = [p for p in binpaths if os.path.exists(p)]
if binpaths:
    os.environ["PATH"] = "%s:%s" % (":".join(binpaths), os.environ["PATH"])
#
##

def conda_package_url(name, version=None, label="main"):
    system = platform.system().lower()
    machine = platform.machine()
    fd = urlopen("http://api.anaconda.org/package/{}".format(name))
    data = json.load(fd)
    fd.close()
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

def prepare_dest(dest):
    destdir = os.path.dirname(dest)
    if not os.path.exists(destdir):
        os.makedirs(destdir)

def conda_package_extract(conda_url, prefix):
    print("downloading {}".format(conda_url))
    localfile = urlretrieve(conda_url)[0]
    fmt = conda_url.split(".")[-1]
    def match_member(m):
        return m.name.split('/')[0] != 'info'
    with tarfile.open(localfile, "r:%s"%fmt) as tar:
        for m in tar:
            if match_member(m):
                dest = os.path.join(prefix, m.name)
                print("installing %s" % dest)
                tar.extract(m, prefix)
    os.unlink(localfile)

def is_installed(progname):
    if sys.version_info[0] < 3:
        paths = os.environ["PATH"].split(":")
        for p in paths:
            if os.path.exists(os.path.join(p, progname)):
                return True
        return False
    return shutil.which(progname) is not None

def installation_prefix():
    if platform.system() == "Windows":
        return PREFIXES[0]
    if os.getuid() == 0:
        return PREFIXES[0]
    else:
        return PREFIXES[-1]

def setup(*specs):
    if os.path.exists(os.path.join(sys.prefix, 'conda-meta')):
        print("You seem to be within a conda environment, nothing to do.")
        return
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-f", "--force", default=False, action="store_true",
            help="Force installation")
    args = parser.parse_args()
    prefix = installation_prefix()
    for spec in specs:
        name = spec["pkg"].split('/')[-1]
        if not args.force:
            print("# checking for {}".format(name))
            skip = True
            for prog in spec.get("check_progs", []):
                if not is_installed(prog):
                    skip = False
                    break
            if skip and "check_install" in spec:
                skip = spec["check_install"]()
            if skip:
                print("# {} is already installed.".format(name))
                continue
        print("# installing {} in {}".format(spec["pkg"], prefix))
        pkg = conda_package_url(spec["pkg"])
        if pkg is None:
            print("Error: no package found for your system!")
            continue
        conda_package_extract(pkg, prefix)

PKG = {
    "clingo": {"pkg": "colomoto/clingo", "check_progs": ["clingo"]},
    "ginsim": {"pkg": "colomoto/ginsim", "check_progs": ["GINsim"]},
    "nusmv": {"pkg": "colomoto/nusmv", "check_progs": ["NuSMV"]},
    "its": {"pkg": "colomoto/its", "check_progs": ["its-reach", "its-ctl"]},
}

