
import json
import random

def wui_sources(name, label=None, color=None, menu=None, toolbar=None, js_api={}):
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

    js_api = ",\n".join(["%s: %s" % item for item in js_api.items()])

    ssid = "colomoto-setup-{}".format(random.randint(1, 10**7))

    setup_js = """
    var {name}_jsapi = {{ {js_api} }};
    colomoto_extension(Jupyter, "{ssid}", "{name}", {menu}, {toolbar}, {name}_jsapi);
    """
    setup_js = setup_js.format(name=name,
                                ssid=ssid,
                                menu=menu_js,
                                toolbar=toolbar_js,
                                js_api=js_api)

    return {"js": setup_js, "css": src_css, "ssid": ssid}

