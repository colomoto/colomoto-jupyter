from colomoto_jupyter import IN_IPYTHON, HAS_IPYLAB, jupyter_setup

if IN_IPYTHON:
    from IPython.display import display, FileLink

    menu = [
        {"name": "Load model", "snippet": 'model = demo_tool.load("filename")'},
        {
            "name": "Upload models",
            "snippet": "demo_tool.upload_many('model')",
        },  # use lists for multiple lines
        "---",
        {
            "name": "Model export",
            "sub-menu": [
                {"name": "Format 1 (.f1)", "snippet": 'model.export("model.f1")'},
                {"name": "Format 2 (.f2)", "snippet": 'model.export("model.f2")'},
            ],
        },
        {
            "name": "About",
            "sub-menu": [
                {"name": "CoLoMoTo", "external-link": "https://colomoto.github.io/"},
                {
                    "name": "CoLoMoTo Jupyter",
                    "external-link": "https://github.com/colomoto/colomoto-jupyter",
                },
            ],
        },
    ]

    toolbar = [
        {
            "name": "upload",
            "setup": {
                "icon": "fa fa-upload",
                "label": __name__,
                "help": "Upload model",
                "handler": "insert_snippet",
                "args": {"snippet": f"{__name__}.upload('model')"},
            },
        },
    ]

    js_api = {}

    jupyter_setup(
        __name__,
        label="Test",
        color="white",
        bgcolor="lightblue",
        menu=menu,
        toolbar=toolbar,
        js_api=js_api,
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


if IN_IPYTHON and HAS_IPYLAB:

    from colomoto_jupyter.upload import jupyter_upload

    def upload(model_var: str):
        return jupyter_upload(__name__, model_var, "load")

    from colomoto_jupyter.ipylab import (
        ipylab_insert_run_snippet,
        ipylab_upload_and_process_filenames,
    )

    def upload_many(model: str):
        def callback(filenames: list[str]):
            snippet = []
            i = 0
            for filename in filenames:
                snippet.append(f"{model}_{i} = {__name__}.load('{filename}')")
                i += 1
            snippet.append(", ".join([f"{model}_{i}" for i in range(0,i)]))
            ipylab_insert_run_snippet(snippet)

        ipylab_upload_and_process_filenames(callback)
