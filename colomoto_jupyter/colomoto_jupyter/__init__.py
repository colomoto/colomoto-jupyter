
import os
import json

import networkx as nx

basedir = os.path.join(os.path.dirname(__file__))

try:
    get_ipython()
    IN_IPYTHON = True
except NameError:
    IN_IPYTHON = False

if IN_IPYTHON:
    from IPython.display import display, HTML

def svg_of_graph(g):
    """
    Returns SVG representation of ``networkx.Graph`` `g` with GraphViz dot layout.
    """
    dbg("computing graph layout...")
    return nx.nx_pydot.to_pydot(g).create_svg().decode()

__GLOBAL_INSTALL_DONE = False

def install_default_formatters():
    """
    Register default IPython formatters:

    * ``networkx.Graph`` with :py:func:`.svg_of_graph`
    """
    ip = get_ipython()
    # nxgraph to svg
    svg_formatter = ip.display_formatter.formatters["image/svg+xml"]
    svg_formatter.for_type(nx.Graph, svg_of_graph)

def jupyter_js(data, autoclean=True):
    return """<script type="text/javascript"%s>
        if (typeof Jupyter != 'undefined') {
            %s }</script>""" % (' class="to-be-removed"' if autoclean else "", data)

def jupyter_setup(name, label=None, color=None, menu=None, toolbar=None, js_api=""):
    global __GLOBAL_INSTALL_DONE
    if not __GLOBAL_INSTALL_DONE:
        jsfile = os.path.join(basedir, "jupyter_ext.js")
        install_default_formatters()
        with open(jsfile) as f:
            display(HTML(jupyter_js(f.read())))
        __GLOBAL_INSTALL_DONE = True
    if not menu and not toolbar:
        return

    args = {
        "name": name,
        "label": label,
        "color": color,
    }

    menu_js = json.dumps({"name": label, "sub-menu": menu}) if menu else "null"
    menu_css = """
    #{name}_menu {{
        color: {color};
        background-color: white;
    }}
    """.format(**args) if menu else ""

    toolbar_js = json.dumps(toolbar) if toolbar else "null"
    toolbar_css = """
    div#{name}-toolbar:before {{
        content: "{label}";
        float: left;
        margin-left: 1em;
        margin-right: 1em;
        margin-top: 0.2em;
    }}
    div#{name}-toolbar,
    div#{name}-toolbar button {{
        color: {color};
    }}
    """.format(**args) if toolbar else ""

    src_css = '<style type="text/css">%s%s</style>' % (menu_css, toolbar_css)

    setup_js = """
    var {name}_jsapi = {{ {js_api} }};
    colomoto_extension(Jupyter, "{name}", {menu}, {toolbar}, {name}_jsapi);
    """
    setup_js = setup_js.format(name=name,
                                menu=menu_js,
                                toolbar=toolbar_js,
                                js_api=js_api)
    src_js = jupyter_js(setup_js)

    display(HTML("%s%s" % (src_css, src_js)))


__ALL__ = ["IN_IPYTHON",
    "jupyter_js",
    "jupyter_setup",
]

