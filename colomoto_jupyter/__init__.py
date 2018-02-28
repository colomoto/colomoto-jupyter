
import os
import json
import base64

from .formatters import install_default_formatters
from .wui import wui_sources

basedir = os.path.join(os.path.dirname(__file__))

try:
    get_ipython()
    IN_IPYTHON = True
except NameError:
    IN_IPYTHON = False

if IN_IPYTHON:
    from IPython.display import display, HTML, Image, Markdown

    def hello():
        docker_image = os.getenv("DOCKER_IMAGE")
        if docker_image:
            docker_date = os.getenv("DOCKER_BUILD_DATE")

            docker_name, docker_tag = docker_image.split(":")

            # remove global namespace
            parts = docker_name.split("/")
            if len(parts) > 2:
                docker_name = "/".join(parts[-2:])

            if docker_tag in ["next", "latest"] and docker_date:
                label = "`{}` built on `{}`".format(docker_name, docker_date)
            else:
                label = "`{}:{}`".format(docker_name, docker_tag)

            msg = "This notebook has been executed using the docker image %s" % label
            display(Markdown(msg))

    hello()


if IN_IPYTHON:
    def URL(url):
        return Markdown("[{0}]({0})".format(url))
else:
    def URL(url):
        return url

def import_colomoto_tool(modname):
    """
    Import the module `modname` and make it available globally when in IPython.

    Usage:

    >>> modname = import_colomoto_tool("modname")
    """
    mod = __import__(modname, globals(), locals())
    if IN_IPYTHON:
        import builtins
        attr = modname.split(".")[0]
        if not hasattr(builtins, attr):
            setattr(builtins, attr, mod)
    return mod

def jupyter_js(data, autoclean=True, **args):
    if autoclean:
        args["class"] = "to-be-removed"
    args = " ".join(['%s="%s"' % it for it in args.items()]) if args else ""
    return """<script type="text/javascript" %s>
        if (typeof Jupyter != 'undefined') {
            %s }</script>""" % (args, data)

def disp_jupyter_js(data, **opts):
    display(HTML(jupyter_js(data, **opts)))

__GLOBAL_INSTALL_DONE = False
def jupyter_setup(*args, **kwargs):
    js_src = ""
    css_src = ""
    global __GLOBAL_INSTALL_DONE
    if not __GLOBAL_INSTALL_DONE:
        jsfile = os.path.join(basedir, "jupyter_ext.js")
        install_default_formatters()
        with open(jsfile) as f:
            js_src = f.read()
        __GLOBAL_INSTALL_DONE = True

    jsargs = {}
    if "menu" in kwargs or "toolbar" in kwargs:
        wui_src = wui_sources(*args, **kwargs)
        js_src += wui_src["js"]
        css_src += wui_src["css"]
        if "ssid" in wui_src:
            jsargs["id"] = wui_src["ssid"]

    js_src = jupyter_js(js_src, **jsargs)
    display(HTML("%s%s" % (js_src, css_src)))

def show_image(data):
    if isinstance(data,str):
        data = base64.b64decode(data)
    return Image(data=data)


