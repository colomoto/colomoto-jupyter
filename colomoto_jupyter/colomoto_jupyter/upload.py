
import base64
import random

from IPython.display import display, HTML

from .sessionfiles import new_output_file

import sys

def _jupyter_upload_callback(data):
    filename = new_output_file(suffix="_%s" % data["name"])
    content = base64.b64decode(data["content"].split(",")[1])
    content = content.decode("utf-8")
    with open(filename, 'w') as f:
        f.write(content)
    print(filename,end='')
    return filename

get_ipython().push({"colomoto_default_upload_callback": _jupyter_upload_callback})

def jupyter_upload(call_orig, call_dest,
        py_callback="colomoto_default_upload_callback"):
    args = {
        "ssid": "colomoto-loading-{}".format(random.randint(1, 10**7)),
        "orig": call_orig,
        "dest": call_dest,
        "py_callback": py_callback,
    }
    return display(HTML("""<input type="file" id="{ssid}"
        onchange="colomoto_upload(Jupyter, '{ssid}', this,
            '{py_callback}', '{orig}', '{dest}')">""".format(**args)))


