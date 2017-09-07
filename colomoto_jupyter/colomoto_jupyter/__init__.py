
import os
import json

from .formatters import install_default_formatters
from .wui import wui_sources

basedir = os.path.join(os.path.dirname(__file__))

try:
    get_ipython()
    IN_IPYTHON = True
except NameError:
    IN_IPYTHON = False



def jupyter_js(data, autoclean=True):
    return """<script type="text/javascript"%s>
        if (typeof Jupyter != 'undefined') {
            %s }</script>""" % (' class="to-be-removed"' if autoclean else "", data)

if IN_IPYTHON:
    from IPython.display import display, HTML

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

    if "menu" in kwargs or "toolbar" in kwargs:
        wui_src = wui_sources(*args, **kwargs)
        js_src += wui_src["js"]
        css_src += wui_src["css"]

    js_src = jupyter_js(js_src)
    display(HTML("%s%s" % (js_src, css_src)))


__ALL__ = ["IN_IPYTHON",
    "jupyter_js",
    "jupyter_setup",
]

