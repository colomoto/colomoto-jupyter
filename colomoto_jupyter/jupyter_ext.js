
function detect_import(cell, module) {
    var code = cell.get_text();
    code = code.replace(/\\\n/g, "");
    var lines = code.split("\n");
    var r_simple = new RegExp("^("+module+")$");
    var r_alias = new RegExp("^"+module+"\\s+as\\s+(\\w+)$");
    for (var i = 0; i < lines.length; ++i) {
        if (/^import\s/.test(lines[i])) {
            code = lines[i].substr(7);
            var parts = code.split(",")
            for (var j = 0; j < parts.length; ++j) {
                code = parts[j].trim();
                var m = code.match(r_simple);
                if (!m) {
                    m = code.match(r_alias);
                }
                if (m) {
                    return m[1];
                }
            }
        }
    }
    return module;
}

function colomoto_replace_call(cell, orig, dest, args, comment=false) {
    var call_regexp = new RegExp("\\."+orig.replace(".","\\.")+"\\(");
    var call_replacer = new RegExp("\\."+orig.replace(".","\\.")
                    + "\\(\\s*([^\\)]*)?\\)");
    var code = cell.get_text();
    var lines = code.split("\n");
    if (args) {
        var strargs = ", "+args.join(", ");
    } else {
        var strargs = "";
    }
    for (var i = 0; i < lines.length; ++i) {
        if (call_regexp.test(lines[i])) {
            var code = ""
            if (comment) {
                code += "#"+lines[i]+"\n";
            }
            code += lines[i].replace(call_replacer, "."+dest+"($1"+strargs+")")
            lines[i] = code;
        }
    }
    cell.set_text(code)
}

function colomoto_upload(Jupyter, ssid, input, py_callback_name, orig, dest) {

    function callback(out_data) {
        var cell_element = $("#"+ssid).parents('.cell');
        var cell_idx = Jupyter.notebook.get_cell_elements().index(cell_element);
        var cell = Jupyter.notebook.get_cell(cell_idx);

        var filename = out_data.content.text;

        var code = cell.get_text();
        code = code.replace(new RegExp("\\b" + orig.replace('.', '\\.')
                    + "\\(\\s*((\\w+)=[^\\)]*)?\\)"),
                dest+"(\""+filename+"\",$1)");
        code = code.replace('",)', '")')
        cell.set_text(code);

        Jupyter.notebook.select(cell_idx);
        Jupyter.notebook.execute_cell_and_select_below();
    }

    if (! (window.File && window.FileReader && window.FileList && window.Blob)) {
        alert("Interactive file upload is not supported by your browser.");
        return;
    }

    input.disabled = true;
    input.style.cursor = "wait";
    input.parentElement.style.cursor = "wait";

    var f = input.files[0];
    var reader = new FileReader();
    reader.onload = (function(f) {
        return function (e) {
            var obj = {
                content: e.target.result,
                name: f.name
            };

            //var pycb = py_callback_name+"("+JSON.stringify(obj)+")"
            // hack/workaround:
            // it seems that Jupyter does not like very long lines
            // so we split the data in chunks
            var chunk_length = 100;
            var pycb = "__colomoto_upload_name = " + JSON.stringify(obj.name) + "\n";
            pycb += "__colomoto_upload_content = \\\n";
            for (var i = 0; i < obj.content.length; i += chunk_length) {
                pycb += "\"" + obj.content.substr(i, chunk_length)+"\"\\\n"
            }
            pycb += "\n"
            pycb += py_callback_name+"({'name':__colomoto_upload_name, 'content': __colomoto_upload_content})\n";
            pycb += "del __colomoto_upload_name, __colomoto_upload_content"

            IPython.notebook.kernel.execute(pycb, {iopub: {output: callback}});
        };
    })(f);
    reader.readAsDataURL(f);
}

function resolve_function(tool_api, funcname) {
    if (tool_api.hasOwnProperty(funcname)) {
        return tool_api[funcname];
    } else {
        return window[funcname];
    }
}

function colomoto_extension(Jupyter, ssid, name, menu, toolbar, tool_api) {

    function insert_snippet_code(snippet) {
        var cell = Jupyter.notebook.get_selected_cell();
        Jupyter.notebook.edit_mode();
        cell.code_mirror.replaceSelection(snippet, 'around');
        //cell.focus_editor();
    }

    /**
        from https://github.com/moble/jupyter_boilerplate/blob/master/main.js
    */
    function callback_insert_snippet (evt) {
        // this (or event.currentTarget, see below) always refers to the DOM
        // element the listener was attached to - see
        // http://stackoverflow.com/questions/12077859
        insert_snippet_code($(evt.currentTarget).data('snippet-code'));
    }
    function build_menu_element (menu_item_spec, direction) {
        // Create the menu item html element
        var element = $('<li/>');

        if (typeof menu_item_spec == 'string') {
            if (menu_item_spec != '---') {
                return element.html(menu_item_spec)
                        .addClass('ui-state-disabled')
                        .attr({"style": "padding:2px .4em"})
                       ;
            }
            return element.addClass('divider');
        }

        var a = $('<a/>')
            .attr('href', '#')
            .html(menu_item_spec.name)
            .appendTo(element);
        if (menu_item_spec.hasOwnProperty('snippet')) {
            var snippet = menu_item_spec.snippet;
            if (typeof snippet == 'string' || snippet instanceof String) {
                snippet = [snippet];
            }
            a.attr({
                'title' : "", // Do not remove this, even though it's empty!
                'data-snippet-code' : snippet.join('\n'),
            })
            .on('click', callback_insert_snippet)
            .addClass('snippet');
        }
        else if (menu_item_spec.hasOwnProperty('internal-link')) {
            a.attr('href', menu_item_spec['internal-link']);
        }
        else if (menu_item_spec.hasOwnProperty('external-link')) {
            a.empty();
            a.attr('href', menu_item_spec['external-link']);
            a.attr({
                'target' : '_blank',
                'title' : 'Opens in a new window',
            });
            $('<i class="fa fa-external-link menu-icon pull-right"/>').appendTo(a);
            $('<span/>').html(menu_item_spec.name).appendTo(a);
        }

        if (menu_item_spec.hasOwnProperty('sub-menu')) {
            element
                .addClass('dropdown-submenu')
                .toggleClass('dropdown-submenu-left', direction === 'left');
            var sub_element = $('<ul class="dropdown-menu"/>')
                .toggleClass('dropdown-menu-compact', menu_item_spec.overlay === true) // For space-saving menus
                .appendTo(element);

            var new_direction = (menu_item_spec['sub-menu-direction'] === 'left') ? 'left' : 'right';
            for (var j=0; j<menu_item_spec['sub-menu'].length; ++j) {
                var sub_menu_item_spec = build_menu_element(menu_item_spec['sub-menu'][j], new_direction);
                if(sub_menu_item_spec !== null) {
                    sub_menu_item_spec.appendTo(sub_element);
                }
            }
        }

        return element;
    }

    function menu_setup (menu_item_specs, sibling, insert_before_sibling) {
        for (var i=0; i<menu_item_specs.length; ++i) {
            var menu_item_spec;
            if (insert_before_sibling) {
                menu_item_spec = menu_item_specs[i];
            } else {
                menu_item_spec = menu_item_specs[menu_item_specs.length-1-i];
            }
            var direction = (menu_item_spec['menu-direction'] == 'left') ? 'left' : 'right';
            var menu_element = build_menu_element(menu_item_spec, direction);
            // We need special properties if this item is in the navbar
            if ($(sibling).parent().is('ul.nav.navbar-nav')) {
                menu_element
                    .addClass('dropdown')
                    .removeClass('dropdown-submenu dropdown-submenu-left');
                menu_element.children('a')
                    .addClass('dropdown-toggle')
                    .attr({
                        'id': name+'_menu',
                        'data-toggle' : 'dropdown',
                        'aria-expanded' : 'false'
                    });
            }

            // Insert the menu element into DOM
            menu_element[insert_before_sibling ? 'insertBefore': 'insertAfter'](sibling);
        }
    }
    /** end from */


    function self_cleanup() {
        var cell_element = $("script[class='to-be-removed']").parents('.cell');
        var cell_idx = Jupyter.notebook.get_cell_elements().index(cell_element);
        var cell = Jupyter.notebook.get_cell(cell_idx);
        var to_remove = -1;
        for (var i = 0; i < cell.output_area.outputs.length; ++i) {
            var oa = cell.output_area.outputs[i];
            if (oa.output_type == "display_data"
                && typeof oa.data["text/html"] != 'undefined'
                && oa.data["text/html"].indexOf(' class="to-be-removed"') >= 0) {
                to_remove = i;
                break;
            }
        }
        if (to_remove == -1) {
            console.log("cannot find toberemoved");
        } else {
            cell.output_area.outputs.splice(to_remove, 1);
        }
    }

    function toolbar_setup(actions) {
        var buttons = [];
        for (var i = 0; i < actions.length; ++i) {
            var setup = actions[i].setup;
            if (typeof setup.handler == 'string') {
                setup.handler = resolve_function(tool_api, setup.handler);
            }
            buttons.push(Jupyter.actions.register(actions[i].setup,
                actions[i].name, name));
        }
        $("#"+name+"-toolbar").remove();
        Jupyter.toolbar.add_buttons_group(buttons, name+"-toolbar");
    }

    function replace_menu_snippets(menu_spec, orig, dest) {
        if (menu_spec.hasOwnProperty("snippet")) {
            var snippet = menu_spec.snippet;
            if (typeof snippet == "string" || snippet instanceof String) {
                menu_spec["snippet"] = snippet.replace(orig, dest);
            } else {
                for (var i = 0; i < snippet.length; ++i) {
                    menu_spec["snippet"][i] = snippet[i].replace(orig, dest);
                }
            }
        }
        if (menu_spec.hasOwnProperty("sub-menu")) {
            for (var i = 0; i < menu_spec["sub-menu"].length; ++i) {
                replace_menu_snippets(menu_spec["sub-menu"][i], orig, dest);
            }
        }
    }

    function load_ipython_extension() {

        var mycellelt = $("#"+ssid).parents('.cell');
        var myidx = Jupyter.notebook.get_cell_elements().index(mycellelt);
        var import_cell = Jupyter.notebook.get_cell(myidx);

        var alias = detect_import(import_cell, name);
        tool_api.module_alias = alias;
        if (alias && alias != name) {
            var orig = new RegExp("\\b"+name+"\\b", "g");
            replace_menu_snippets(menu, orig, alias);
        }

        if (toolbar) {
            toolbar_setup(toolbar);
        }

        $("#"+name+"_menu").parent().remove();
        if (menu) {
            menu_setup([menu], $("#help_menu").parent(), true);
        }

        if (tool_api.hasOwnProperty("post_install_callback")) {
            tool_api.post_install_callback();
        }

        setTimeout(self_cleanup, 5000);
    };

    load_ipython_extension();
}

function resolve_toolbar_handlers(tool_api, toolbar_spec) {
    for (var i = 0; i < toolbar_spec.length; ++i) {
        func = resolve_function(tool_api, toolbar_spec[i]["setup"]["handler"]);
        toolbar_spec[i]["setup"]["handler"] = func;
    }
    return toolbar_spec
}

