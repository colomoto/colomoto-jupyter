from typing import Callable, Any

from IPython.display import display, HTML
from ipylab import JupyterFrontEnd
from ipywidgets import widgets, interact
from .upload import new_output_file

_jupyter_front_end = JupyterFrontEnd()
"""Global objet to access Jupyter widgets through IPyLab API."""

_installed_modules: set[str] = set()
"""A set gathering identifiers of already installed UI of modules"""


def ipylab_front_end() -> JupyterFrontEnd:
    """Return the singleton object used to access Jupyter frontend."""
    assert _jupyter_front_end is not None
    return _jupyter_front_end


def ipylab_insert_snippet(snippet: str | list[str], run_it: bool = False) -> None:
    """Insert a snippet into the Jupyter front end."""
    runpref = "run-" if run_it else ""
    _jupyter_front_end.commands.execute(f"custom-menu:{runpref}snippet", snippet)


def ipylab_insert_run_snippet(snippet: str | list[str]) -> None:
    """Insert and run a _snippet_ into the Jupyter front end."""
    ipylab_insert_snippet(snippet, run_it=True)


def ipylab_upload_and_process_filenames(
    process: Callable[[list[str], dict], None], **process_data
) -> None:
    def upload_callback_(files, **data):
        filenames = []
        for file in files:
            filename = new_output_file(suffix="_%s" % file["name"])
            with open(filename, "wb") as f:
                f.write(file["content"])
            filenames.append(filename)
        process(filenames, **data)
    ipylab_upload_and_process_data(upload_callback_, allow_multiple = True,
                                   **process_data)

def ipylab_upload_and_process_filename(
    process: Callable[[str, dict], None], **process_data
) -> None:
    def upload_callback_(files, **data):
        file = files[0]
        filename = new_output_file(suffix="_%s" % file["name"])
        with open(filename, "wb") as f:
            f.write(file["content"])
        process(filename, **data)
    ipylab_upload_and_process_data(upload_callback_, **process_data)


def ipylab_upload_and_process_data(process, *, allow_multiple = False, **process_data):
    def upload_callback_(filespecs):
        if not filespecs:
            display(HTML(f"<b>No file selected.</b>"))
        else:
            process(filespecs, **process_data)
    uploader = widgets.FileUpload(multiple=allow_multiple)
    interact(upload_callback_, filespecs=uploader)


def ipylab_ui_setup(
    module_name: str,
    *,
    label: str = None,
    menu: list[dict | str] = None,
    toolbar: list[dict] = None,
    color: str = None,
    bgcolor: str = None,
) -> None:
    """
    Install a new menu and toolbar buttons to the underlying Notebook.

    The extension of the UI is registered under the name `module_name`.

    The created menu is labeled with `label`. `color` and `bgcolor` specify
    respectively the color of characters and the background color used to display
    the menu.

    A menu entry is either a string or a dictionary. A string "---" or
    "separator" specifies the entry is displayed as a separation line in the
    menu. Other types of entries contain two keys:
    - `name` that specifies the label displayed for the menu entry.
    - a payload key that depends on the kind of entry:
        * `snippet` specifies the payload is a string that has to be
        inserted in the current cell of the notebook.
        * `run-snippet` behaves like 'snippet' but also executes the inserted
        code.
        * `external-link` indicates the payload is a URL and the entry is a
        hyperlink to it.
        * `sub-menu` specifies the payload is a menu description.
        * `command` is either a string or a callable. The string is the
        identifier of an existing command in the Notebook (see method
        `ipylab.commands.CommandRegistry.add_command)`_. If a callable is used,
        then it is invoked with no arguments.

    In `toolbar`, buttons are specified by dictionaries containing two keys:
    - `name` identifies the button.
    - `setup` is a dictionary containing the following settings:
        * `handler` is the callback invoked when the button is clicked. It can
           be either a string containing the identifier of an already existing
           Notebook command or a callable object (in which case, a new command
           is created).
        * `args` are the arguments passed to the callback.
        * `icon` is a string containing the class name of the icon (e.g. 'fa fa-upload')
        * `tooltip` is the tooltip displayed when the mouse hovers the button.
        * `label` is a string used to label the button.
        * `color` specifies the color of the label. If this field is None,
        the parameter `color` is used.
        * `bgcolor` specifies the background color of the label. If this field
        is None, the parameter `bgcolor` is used.
    """

    if module_name in _installed_modules:
        return
    _installed_modules.add(module_name)
    if menu is not None:
        _setup_menu(module_name, label, menu, color, bgcolor)
    if toolbar is not None:
        _setup_toolbar(module_name, toolbar, color, bgcolor)


__all__ = (
    "ipylab_front_end",
    "ipylab_insert_snippet",
    "ipylab_insert_run_snippet",
    "ipylab_ui_setup",
)


def _setup_menu(
    module_name: str,
    label: str,
    menu: list[dict | str],
    color: str = None,
    bgcolor: str = None,
) -> None:
    def add_command(label, command_name, cmd) -> str:
        try:
            _jupyter_front_end.commands.add_command(command_name, execute=cmd, label=label)
            return command_name
        except:
            pass
        return None

    def generate_snippets(title : str, menuspec : list[dict | str]) -> list[dict | str]:
        result = []
        for entry in menuspec:
            newentry = {}
            if isinstance(entry, str):
                newentry = entry
            elif "name" not in entry:
                raise Exception("invalid menu entry '{entry}'; 'name' is missing.")
            else:
                name = entry["name"]
                if "command" in entry:
                    newentry["command"] = entry["command"]
                elif "sub-menu" in entry:
                    newentry["sub-menu"] = generate_snippets(f"{title}:{name}", entry["sub-menu"])
                elif "external-link" in entry:
                    def cmd(url):
                        return lambda: _jupyter_front_end.commands.execute("help:open", {"url": url})
                    command_name = f"custom-menu:open-url:{title}:{name}"
                    newentry["command"] = add_command(name, command_name, cmd(entry["external-link"]))
                elif "snippet" in entry:
                    def cmd(snippet):
                        return lambda: _jupyter_front_end.commands.execute(
                            "custom-menu:snippet", snippet
                        )
                    command_name = f"custom-menu:snippet:{title}:{name}"
                    newentry["command"] = add_command(name, command_name, cmd(entry["snippet"]))
                elif "run-snippet" in entry:
                    def cmd(snippet):
                        return lambda: _jupyter_front_end.commands.execute(
                            "custom-menu:run-snippet", snippet
                        )
                    command_name = f"custom-menu:run-snippet:{title}:{name}"
                    newentry["command"] = add_command(name, command_name, cmd(entry["run-snippet"]))
                else:
                    raise Exception(f"unknown menu entry '{entry}'")
                newentry["name"] = name
                result.append(newentry)
        return result

    menu_classname = f"{module_name}-menu"
    actual_menu = generate_snippets(label, menu)
    _jupyter_front_end.menu.add_menu(label, actual_menu, menu_classname)
    _setup_css_for_menu_(menu_classname, color, bgcolor)


def _setup_css_for_menu_(menu_classname, color=None, bgcolor=None) -> None:
    strcolor = f"color : {color};" or ""
    strbgcolor = f"background-color : {bgcolor};" or ""

    css = ""
    if color or bgcolor:
        css += f""".{menu_classname} {{ {strcolor} {strbgcolor} }}"""

    if css != "":
        display(HTML(f"""<style>{css}</style>"""))


def _setup_toolbar(
    module_name: str,
    toolbar: dict,
    default_color: str = None,
    default_bgcolor: str = None,
) -> None:
    for button_spec in toolbar:
        button_name = f"{module_name}_{button_spec['name']}"
        setup = button_spec["setup"]
        _jupyter_front_end.toolbar.add_button(
            button_name,
            execute=setup["handler"],
            args=setup.get("args", {}),
            iconClass=setup.get("icon", None),
            after=setup.get("after", "cellType"),
            tooltip=setup.get("help", None),
            className=f"{module_name}-toolbar {button_name}-toolbar-button",
        )
        toolbar_class = f"{module_name}-toolbar"
        button_class = f"{button_name}-toolbar-button"
        _setup_css_for_toolbar_button(
            toolbar_class,
            button_class,
            label=setup.get("label", None),
            color=setup.get("color", default_color),
            bgcolor=setup.get("bgcolor", default_bgcolor),
        )


def _setup_css_for_toolbar_button(
    toolbar_class, button_class, label=None, color=None, bgcolor=None
) -> None:
    strcolor = f"color : {color};" or ""
    strbgcolor = f"background-color : {bgcolor};" or ""

    css = ""
    if color or bgcolor:
        css += f""".{toolbar_class}, .{button_class} {{ {strcolor} {strbgcolor} }}"""

    if label:
        css += f""".{button_class}:before {{
            content: '{label}';
            float: left;
            margin-left: 1em;
            margin-right: 1em;
            margin-top: 0.2em;
        }}"""
    if css != "":
        display(HTML(f"""<style>{css}</style>"""))
