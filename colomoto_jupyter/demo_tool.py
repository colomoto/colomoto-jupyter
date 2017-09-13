
from colomoto_jupyter import IN_IPYTHON, jupyter_setup

if IN_IPYTHON:
    from IPython.display import display, FileLink

    menu = [
        {"name": "Load model",
            "snippet": "model = demo_tool.load(\"filename\")"},
        {"name":"Upload model",
            "snippet": "model = demo_tool.upload()"}, # use lists for multiple lines
        "---",
        {"name":"Model export",
            "sub-menu": [
            {"name": "Format 1 (.f1)",
                "snippet": 'model.export("model.f1")'},
            {"name": "Format 2 (.f2)",
                "snippet": 'model.export("model.f2")'},
            ]},
    ]

    toolbar = [
        {"name": "upload",
         "setup": {
            "icon": "fa-upload",
            "help": "Upload model",
            "handler": "action_upload_model"}},
    ]
    js_api = {
        "action_upload_model":
            """function () {
            var cell = Jupyter.notebook.get_selected_cell();
            cell.set_text('model = '+demo_tool_jsapi.module_alias+'.upload()');
            cell.focus_editor(); }
            """
    }
    jupyter_setup(__name__,
        label="Test",
        color="blue",
        menu=menu,
        toolbar=toolbar,
        js_api=js_api
    )

class DummyModel:
    def __init__(self, filename):
        self.filename = filename
    def __repr__(self):
        return "<DummyModel: %s>" % self.filename
    def export(self, output):
        with open(output, "w") as out:
            out.write("TEST")
        if IN_IPYTHON:
            display(FileLink(output))

def load(filename):
    return DummyModel(filename)

if IN_IPYTHON:
    from colomoto_jupyter.upload import jupyter_upload
    def upload():
        return jupyter_upload(upload, load)


