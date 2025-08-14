
from colomoto_jupyter.ipylab import (
    ipylab_insert_run_snippet,
    ipylab_upload_and_process_filename,
)

def jupyter_upload(module_name, model_var, call_dest="load"):
    def callback(filename: str):
        ipylab_insert_run_snippet(f"{model_var} = {module_name}.{call_dest}(\"{filename}\")")

    ipylab_upload_and_process_filename(callback)


