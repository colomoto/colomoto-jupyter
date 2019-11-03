
import copy

from colomoto_jupyter import import_colomoto_tool
from colomoto_jupyter.sessionfiles import new_output_file
from colomoto_jupyter import IN_IPYTHON, jupyter_setup

import boolean

if IN_IPYTHON:
    jupyter_setup("minibn", label="miniBN")

class NOT(boolean.NOT):
    def __init__(self, *args):
        super().__init__(*args)
        self.operator = "!"


class BaseNetwork(dict):
    def __init__(self, data=None, Symbol_class=boolean.Symbol,
            allowed_in_name=('.','_',':','-'), **kwargs):
        super().__init__()
        self.ba = boolean.BooleanAlgebra(NOT_class=NOT,
            Symbol_class=Symbol_class,
            allowed_in_token=allowed_in_name)
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

    def import_data(self, data):
        raise NotImplementedError
    def source(self, sep):
        raise NotImplementedError
    def __repr__(self):
        return self.source(sep=" <- ")

    @classmethod
    def load(celf, filename):
        f = celf()
        with open(filename) as data:
            f.import_data(data)
        return f


    def v(self, name):
        return self.ba.symbols(name)[0]
    def vars(self, *names):
        return self.ba.symbols(*names)

    def _autokey(self, a):
        if isinstance(a, self.ba.Symbol):
            a = a.obj
        return a

    def _autobool(self, expr):
        if isinstance(expr, bool):
            return self.ba.TRUE if expr else self.ba.FALSE
        elif isinstance(expr, int):
            return self.ba.TRUE if expr > 0 else self.ba.FALSE
        return expr

    def _normalize_tr(self, tr):
        ntr = {}
        for k, v in tr.items():
            if not isinstance(k, self.ba.Symbol):
                k = self.v(k)
            ntr[k] = self._autobool(v)
        return ntr

    def __call__(self, cfg):
        tr = self._normalize_tr(cfg)
        def _autostate(expr):
            if expr == self.ba.TRUE:
                return 1
            elif expr == self.ba.FALSE:
                return 0
            return expr
        return dict([(a, _autostate(self[a].subs(tr).simplify())) for a in self])

    def rewrite(self, a, tr):
        tr = self._normalize_tr(tr)
        self[a] = self[a].subs(tr).simplify()

    def __setitem__(self, a, f):
        if isinstance(f, str):
            f = self.ba.parse(f)
        f = self._autobool(f)
        return super().__setitem__(self._autokey(a), f)

    def __getitem__(self, a):
        return super().__getitem__(self._autokey(a))

    def copy(self):
        bn = copy.copy(self)
        bn.ba = self.ba
        return bn

    biolqm_format = None
    def to_biolqm(self):
        bnfile = new_output_file(ext=self.biolqm_format)
        with open(bnfile, "w") as f:
            f.write(self.source())
        biolqm = import_colomoto_tool("biolqm")
        return biolqm.load(bnfile)

class BooleanNetwork(BaseNetwork):

    biolqm_format = "bnet"
    def source(self, sep=", "):
        buf = ""
        for a, f in sorted(self.items()):
            if f is self.ba.TRUE:
                f = 1
            elif f is self.ba.FALSE:
                f = 0
            buf += "{}{}{}\n".format(a, sep, f)
        return buf

    def inputs(self):
        return [a for a, f in self.items() if f == self.v(a)]

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

    def simplify(self):
        bn = copy.copy(self)
        for a, f in bn.items():
            bn[a] = f.simplify()
        return bn

    def as_dnf(self):
        def make_lit(l):
            if isinstance(l, self.ba.NOT):
                return (l.args[0].obj, False)
            else:
                return (l.obj, True)
        def make_clause(c):
            if isinstance(c, self.ba.AND):
                lits = c.args
            else:
                lits = [c]
            return list(map(make_lit, lits))
        def make_dnf(f):
            if f is self.ba.TRUE:
                return True
            elif f is self.ba.FALSE:
                return False
            clauses = self.ba.dnf(f)
            if not isinstance(clauses, self.ba.OR):
                clauses = [clauses]
            else:
                clauses = clauses.args

            return list(map(make_clause, clauses))
        return dict([(i,make_dnf(f)) for (i,f) in self.items()])

    def influence_graph(self):
        import networkx as nx
        influences = set()
        ig = nx.MultiDiGraph()
        for a, f in self.items():
            ig.add_node(a)
            for lit in f.simplify().literalize().get_literals():
                if isinstance(lit, boolean.NOT):
                    b = lit.args[0].obj
                    sign = -1
                else:
                    b = lit.obj
                    sign = 1
                influences.add((b,a,sign))
        for (b, a, sign) in influences:
            ig.add_edge(b, a, sign=sign, label="+" if sign > 0 else "-")
        return ig

    def propagate_constants(self):
        csttypes = [boolean.boolean._TRUE, boolean.boolean._FALSE]
        bn = self.copy()
        csts = dict([(i,f) for i, f in bn.items() if type(f) in csttypes])
        while csts:
            new_csts = {}
            for a in bn.keys():
                if a in csts:
                    continue
                bn.rewrite(a, csts)
                if type(bn[a]) in csttypes:
                    new_csts[a] = bn[a]
            for a in csts:
                del bn[a]
            csts = new_csts
        return bn

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
        super().__init__(obj)
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
        return super().__eq__(b)
    def __ne__(a, b):
        if isinstance(a, MVVar) and isinstance(b, int):
            return ~(a/b) | (a/(b+1))
        return super().__eq__(b)
    def __hash__(self):
        return super().__hash__()

class MultiValuedNetwork(BaseNetwork):
    biolqm_format = "mnet"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, Symbol_class=MVVar)

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
            super().rewrite(k, tr)
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


