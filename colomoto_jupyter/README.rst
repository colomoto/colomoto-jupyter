CoLoMoTo helper functions for Juypter integration
-------------------------------------------------

Provides helper functions for integration in the CoLoMoTo Jupyter notebook.
It currently provides:
* injection of menus and toolbars
* interactive file upload
* formatter for ``networkx`` graphs

See also https://github.com/colomoto/colomoto-docker


Quick usage guide
=================

.. code:: python
    from colomoto_jupyter import IN_IPYHON, jupyter_setup

    if IN_IPYTHON:

        # menu specification (list of dict), optional
        menu = [
            {"name": "entry 1",
                "snippet": ["code to be append to the current ceull"]},
            "---", # separation
            {"name": "submenu 1",
                "sub-menu": [
                    {"name": "entry 2",
                        "snippet": ["code example"]},
                ]}
        ]

        # toolbar specification (list of dict), optional
        toolbar = [
            {"name": "Label",
             "setup": {
                "icon": "fa-something",
                "help": "tooltip text",
                "handler": "javascript_function_1"}}
        ]

        ## additional javascript functions, optional
        js_api = """
        javascript_function_1: function () {
            alert("plop");
        },
        javascript_function_2: function () {
            alert("foo");
        }
        """

        jupyter_setup("mymodule",
            label="My module",
            color="blue", # for menu and toolbar
            menu=menu,
            toolbar=toolbar,
            js_api=js_api)

See
`demo_tool.py<https://github.com/colomoto/colomoto-api/blob/master/colomoto_jupyter/demo_tool.py>`_ for a more complete usage example.



