
from colomoto_jupyter import import_colomoto_tool
from colomoto_jupyter.sessionfiles import new_output_file

import boolean

class NOT(boolean.NOT):
    def __init__(self, *args):
        super(NOT, self).__init__(*args)
        self.operator = "!"

class BooleanNetwork(dict):
    def __init__(self, data=None, Symbol_class=boolean.Symbol, **kwargs):
        super(BooleanNetwork, self).__init__()
        self.ba = boolean.BooleanAlgebra(NOT_class=NOT,
            Symbol_class=Symbol_class)
        if data:
            if isinstance(data, str):
                self.import_data(data.split("\n"))
            elif isinstance(data, dict):
                for a, f in data.items():
                    self[a] = f
            else:
                self.import_data(data)
        for a, f in kwargs.items():
            self[a] = f

    def v(self, name):
        return self.ba.symbols(name)[0]
    def vars(self, *names):
        return self.ba.symbols(*names)

    def _autobool(self, expr):
        if isinstance(expr, (bool, int)):
            return self.ba.TRUE if expr else self.ba.FALSE
        return expr

    def _normalize_tr(self, tr):
        for k, v in tr.items():
            tr[k] = self._autobool(v)
        return tr

    def rewrite(self, a, tr):
        tr = self._normalize_tr(tr)
        self[a] = self[a].subs(tr).simplify()

    def _autokey(self, a):
        if isinstance(a, self.ba.Symbol):
            a = a.obj
        return a

    def __setitem__(self, a, f):
        if isinstance(f, str):
            f = self.ba.parse(f)
        f = self._autobool(f)
        return super(BooleanNetwork, self).__setitem__(self._autokey(a), f)

    def __getitem__(self, a):
        return super(BooleanNetwork, self).__getitem__(self._autokey(a))

    def source(self, sep=", "):
        buf = ""
        for a, f in sorted(self.items()):
            if f is self.ba.TRUE:
                f = 1
            elif f is self.ba.FALSE:
                f = 0
            buf += "{}{}{}\n".format(a, sep, f)
        return buf

    def import_data(self, data):
        header = None
        for line in data:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            sep = line.find("<-")
            if sep < 0:
                comma = line.index(",")
                left = line[:comma].strip()
                right = line[comma+1:].strip()
            else:
                left = line[:sep].strip()
                right = line[sep+2:].strip()
            if header is None and (left, right) == ("targets", "factors"):
                header = True
                continue
            self[left] = self.ba.parse(right)

    def __repr__(self):
        return self.source(sep=" <- ")

    @classmethod
    def load(celf, filename):
        f = celf()
        with open(filename) as data:
            f.import_data(data)
        return f

    biolqm_format = "bnet"
    def to_biolqm(self):
        bnfile = new_output_file(ext=self.biolqm_format)
        with open(bnfile, "w") as f:
            f.write(self.source())
        biolqm = import_colomoto_tool("biolqm")
        return biolqm.load(bnfile)

    def to_pint(self):
        pypint = import_colomoto_tool("pypint")
        from pypint.converters import import_minibn
        return import_minibn(self)

class MVVar(boolean.Symbol):
    def __init__(self, obj):
        if isinstance(obj, str):
            parts = obj.split(":")
            if len(parts) > 1:
                try:
                    level = int(parts[-1])
                    obj = (":".join(parts[:-1]), level)
                except ValueError:
                    pass
        super(MVVar, self).__init__(obj)
    def is_instanciated(self):
        return isinstance(self.obj, tuple)
    def nodevar(self):
        if self.is_instanciated():
            return self.obj[0]
        return self
    def level(self):
        assert self.is_instanciated()
        return self.obj[1]
    def __str__(self):
        if self.is_instanciated():
            return "{}:{}".format(*self.obj)
        else:
            return "{}".format(self.obj)
    def __truediv__(self, i):
        assert not self.is_instanciated() and isinstance(i, int), repr(self.obj)
        return self.Symbol((self.obj, i))
    def __lt__(a, b):
        assert isinstance(a, MVVar)
        if isinstance(b, MVVar):
            def getobj(mv):
                return mv.obj if mv.is_instanciated() else (mv.obj, 1)
            return getobj(a) < getobj(b)
        if isinstance(b, int):
            return ~(a / b)
        raise NotImplemented
    def __le__(a, b):
        assert isinstance(a, MVVar) and isinstance(b, int)
        return ~(a/(b+1))
    def __gt__(a, b):
        assert isinstance(a, MVVar) and isinstance(b, int)
        return a/(b+1)
    def __ge__(a, b):
        assert isinstance(a, MVVar) and isinstance(b, int)
        return a/b
    def __eq__(a, b):
        if isinstance(a, MVVar) and isinstance(b, int):
            return (a/b) & ~(a/(b+1))
        return super(MVVar, a).__eq__(b)
    def __ne__(a, b):
        if isinstance(a, MVVar) and isinstance(b, int):
            return ~(a/b) | (a/(b+1))
        return super(MVVar, a).__eq__(b)
    def __hash__(self):
        return super(MVVar, self).__hash__()

class MultiValuedNetwork(BooleanNetwork):
    biolqm_format = "mnet"
    def __init__(self, *args, **kwargs):
        super(MultiValuedNetwork, self).__init__(*args, **kwargs, Symbol_class=MVVar)

    def _normalize(self, a, spec):
        (va,) = self.vars(a)
        if isinstance(spec, dict):
            return [(va/i, f)  for i, f in sorted(spec.items())]
        elif isinstance(spec, boolean.Expression):
            return [(va, spec)]
        return spec

    def rewrite(self, a, tr):
        tr = self._normalize_tr(tr)
        k = self._autokey(a.nodevar())
        spec = self[k]
        def _rewrite(expr):
            return expr.subs(tr).simplify()
        if isinstance(spec, boolean.Expression):
            super(MultiValuedNetwork, self).rewrite(k, tr)
        elif isinstance(spec, dict):
            if a.is_instanciated():
                spec[a.level()] = _rewrite(spec[a.level()])
            else:
                for k, f in spec.items():
                    spec[k] = _rewrite(f)
        else:
            if a.is_instanciated():
                def d_rewrite(df):
                    (d,f) = df
                    if d == a:
                        f = _rewrite(f)
                    return (d,f)
            else:
                def d_rewrite(df):
                    (d,f) = df
                    return (d, _rewrite(f))
            self[k] = list(map(d_rewrite, self[k]))

    def append(self, a, f):
        if isinstance(a, str):
            (a,) = self.vars(a)
        if isinstance(f, str):
            f = self.ba.parse(f)
        k = self._autokey(a.nodevar())
        self[k] = self._normalize(k, self[k]) if k in self else []
        self[k].append((a, f))

    def source(self, sep=" <- "):
        buf = ""
        for a, f in sorted(self.items()):
            for d, g in self._normalize(a, f):
                buf += "{}{}{}\n".format(d, sep, g)
        return buf

    def import_data(self, data):
        for line in data:
            line = line.strip()
            if not line:
                continue
            left, right = line.split("<-")
            self.append(left.strip(), right.strip())


