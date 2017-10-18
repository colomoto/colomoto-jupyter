
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

def svg_of_graph(g):
    """
    Returns SVG representation of ``networkx.Graph`` `g` with GraphViz dot layout.
    """
    print("# computing graph layout...")
    return nx.nx_pydot.to_pydot(g).create_svg().decode()


def install_default_formatters():
    """
    Register default IPython formatters:

    * ``networkx.Graph`` with :py:func:`.svg_of_graph`
    """
    ip = get_ipython()
    if HAS_NETWORKX:
        # nxgraph to svg
        svg_formatter = ip.display_formatter.formatters["image/svg+xml"]
        svg_formatter.for_type(nx.Graph, svg_of_graph)

