
import os
import json
import base64

import pandas as pd

from .formatters import install_default_formatters
from .wui import wui_sources

from colomoto import types

basedir = os.path.join(os.path.dirname(__file__))

try:
    get_ipython()
    IN_IPYTHON = True
except NameError:
    IN_IPYTHON = False

if IN_IPYTHON:
    from IPython.display import display, HTML, SVG, Image, Markdown

    pd.set_option("display.max_columns", None)

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
    if os.getenv("COLOMOTO_SKIP_JUPYTER_JS") == "1":
        return ""
    if autoclean:
        args["class"] = "to-be-removed"
    args = " ".join(['%s="%s"' % it for it in args.items()]) if args else ""
    return """<script type="text/javascript" %s>
        if (typeof Jupyter != 'undefined') {
            %s }</script>""" % (args, data)

def disp_jupyter_js(data, **opts):
    if os.getenv("COLOMOTO_SKIP_JUPYTER_JS") != "1":
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
    wui_src = wui_sources(*args, **kwargs)
    js_src += wui_src["js"]
    css_src += wui_src["css"]
    if "ssid" in wui_src:
        jsargs["id"] = wui_src["ssid"]

    js_src = jupyter_js(js_src, **jsargs)
    if os.getenv("COLOMOTO_SKIP_JUPYTER_JS") != "1":
        display(HTML("%s%s" % (js_src, css_src)))

def show_image(data, is_svg=False):
    if is_svg:
        return SVG(data)
    if isinstance(data,str):
        data = base64.b64decode(data)
    return Image(data=data)

def tabulate(data, drop_duplicates=True, reindex=False, sort=True, **kwargs):
    if "columns" not in kwargs:
        drop_duplicates = False

    index = kwargs.get("index")
    level = 0
    if index is None and isinstance(data, list):
        indices = []
        for i, e in enumerate(data):
            if isinstance(e, list):
                level = 1
                indices += [(i,j) for j in range(len(e))]
            else:
                indices.append((i,))
        if level > 0:
            indices = (idx+(0,)*(level-len(idx)+1) for idx in indices)
            index = pd.MultiIndex.from_tuples(indices)
            kwargs["index"] = index
            flat_data = []
            for e in data:
                if isinstance(e, list):
                    flat_data.extend(e)
                else:
                    flat_data.append(e)
            data = flat_data

    df = pd.DataFrame(data, **kwargs)
    if sort:
        df.sort_values(list(df.columns), inplace=True)
        if level > 0:
            level0 = df.index.get_level_values(0).unique()
            lm = dict(zip(level0, range(len(level0))))
            mi = pd.MultiIndex.from_tuples([(lm[l[0]],)+l[1:] for l in df.index])
            df.set_index(mi, inplace=True)
            df.sort_index(level=0, sort_remaining=False, inplace=True)
            mi = pd.MultiIndex.from_tuples([(level0[l[0]],)+l[1:] for l in df.index])
            df.set_index(mi, inplace=True)
    if drop_duplicates:
        df.drop_duplicates(inplace=True)
    if reindex:
        df.reset_index(drop=True, inplace=True)
    if level > 0:
        props = [("display", "none")]
        styles = [{"selector": f"th.level{l}", "props": props} for l in range(1,level+1)]
        styles += [{"selector": f"th.blank.level{l}", "props": props} for l in range(0,level)]
        df = df.style.set_table_styles(styles)
    return df
