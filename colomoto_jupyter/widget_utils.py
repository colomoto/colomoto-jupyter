
import json

from . import IN_IPYTHON

if IN_IPYTHON:
    from IPython.display import display, Javascript
    from IPython.utils.py3compat import str_to_bytes, bytes_to_str

def jupyter_replace_cell_call(orig_func, dest_func, append_args=(),
                                comment=True):
        args = list(map(json.dumps, append_args))
        display(Javascript("""var __cell = Jupyter.notebook.get_selected_cell();
        colomoto_replace_call(__cell, "{}", "{}", {}, {});
        Jupyter.notebook.execute_cell_and_select_below();
        """.format(orig_func, dest_func, json.dumps(args), json.dumps(comment))))


