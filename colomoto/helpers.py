
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

def layout_graph(g, method="dot"):
    """
    Generates layout information for `networkx` graph `g`.
    It returns a `dict` object, with position and size information for nodes,
    and b-spline control points for edges:
    ```
    {"nodes": {
        "node_name": {"x": float, "y": float, "width": float, height: "float"},
        ...},
     "edges": [
        {"tail": "node_name", "head": "node_name",
          "bspline": list[(int x, inty)]},
          ...
       ]}
    ```
    """
    layout = {
        "nodes": {},
        "edges": [],
    }

    lg = nx.nx_pydot.to_pydot(g)
    lg = lg.create_plain(prog=method).decode()
    for line in lg.split("\n"):
        p = line.split()
        if not p:
            continue
        if p[0] == "node":
            layout["nodes"][p[1]] = {
                "x": float(p[2]),
                "y": float(p[3]),
                "width": float(p[4]),
                "height": float(p[5])
            }
        elif p[0] == "edge":
            n = int(p[3])
            spec = {
                "tail": p[1],
                "head": p[2],
                "bspline": [(float(p[2*i+4]),float(p[2*i+5])) for i in range(n)],
            }
            layout["edges"].append(spec)
    return layout

__all__ = []
if HAS_NETWORKX:
    __all__ += ["layout_graph"]
