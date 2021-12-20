
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
    PREFIXES = [os.path.join(os.getenv("APPDATA"), "colomoto")]
    binpaths = [os.path.join(p,"bin") for p in PREFIXES] \
                + [os.path.join(p,"Library","bin") for p in PREFIXES]
    libpaths = [os.path.join(p,"lib") for p in PREFIXES] \
                + [os.path.join(p,"Library","lib") for p in PREFIXES]
else:
    PREFIXES = ["/usr/local/share/colomoto",
        os.path.join(os.path.expanduser("~"), ".local", "share", "colomoto")]
    binpaths = [os.path.join(p, "bin") for p in PREFIXES]
    libpaths = [os.path.join(p, "lib") for p in PREFIXES]

binpaths = [p for p in binpaths if os.path.exists(p)]
if binpaths:
    os.environ["PATH"] = "%s:%s" % (":".join(binpaths), os.environ["PATH"])
libpaths = [p for p in libpaths if os.path.exists(p)]
if libpaths:
    ldpath = os.environ.get("LD_LIBRARY_PATH", "")
    if ldpath:
        libpaths.append(ldpath)
    os.environ["LD_LIBRARY_PATH"] = ":".join(libpaths)
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
        members = [m for m in tar.getmembers() if match_member(m)]
        for m in members:
            dest = os.path.join(prefix, m.name)
            print("installing %s" % dest)
        tar.extractall(prefix, members)
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

def setup(*specs, force=False, force_all=False, parse_args=True):
    if os.path.exists(os.path.join(sys.prefix, 'conda-meta')):
        print("You seem to be within a conda environment, nothing to do.")
        return
    if parse_args:
        from argparse import ArgumentParser
        parser = ArgumentParser()
        parser.add_argument("-f", "--force", default=force, action="store_true",
                help="Force (re)installation of the main dependency")
        parser.add_argument("-F", "--force-all", default=force_all, action="store_true",
                help="Force (re)installation o f all the dependencies")
        args = parser.parse_args()
        force = args.force
        force_all = args.force_all
    prefix = installation_prefix()
    force = force or force_all
    for spec in specs:
        name = spec["pkg"].split('/')[-1]
        if not force:
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
        if not os.path.exists(prefix):
            os.makedirs(prefix)
        pkg = conda_package_url(spec["pkg"])
        if pkg is None:
            print("Error: no package found for your system!")
            continue
        conda_package_extract(pkg, prefix)
        force = force_all

PKG = {
    "clingo": {"pkg": "colomoto/clingo", "check_progs": ["clingo"]},
    "ginsim": {"pkg": "colomoto/ginsim", "check_progs": ["GINsim"]},
    "nusmv": {"pkg": "colomoto/nusmv", "check_progs": ["NuSMV"]},
    "its": {"pkg": "colomoto/its", "check_progs": ["its-reach", "its-ctl"]},
}

