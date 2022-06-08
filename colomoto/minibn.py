
from collections.abc import Hashable
import copy
import hashlib
import itertools
import os
import random
import re
import sys
import tempfile
import unicodedata

import networkx as nx

from colomoto.types import HypercubeCollection
from colomoto_jupyter import import_colomoto_tool
from colomoto_jupyter.io import ensure_localfile
from colomoto_jupyter.sessionfiles import new_output_file
from colomoto_jupyter import IN_IPYTHON, jupyter_setup

import boolean

re_nonword = re.compile(r"\W", flags=re.A)

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
                if "\n" in data or not os.path.exists(data):
                    self.import_data(data.splitlines())
                else:
                    with open(data) as fp:
                        self.import_data(fp)
            elif isinstance(data, dict):
                for a, f in data.items():
                    self[a] = f
            else:
                imported = False
                def biolqm_import(biolqm, lqm):
                    bnfile = new_output_file(self.biolqm_format)
                    assert biolqm.save(lqm, bnfile)
                    with open(bnfile) as fp:
                        self.import_data(fp)
                    return True
                if "biolqm" in sys.modules:
                    biolqm = sys.modules["biolqm"]
                    if biolqm.is_biolqm_object(data):
                        imported = biolqm_import(biolqm, data)
                if not imported and "ginsim" in sys.modules:
                    ginsim = sys.modules["ginsim"]
                    if ginsim.is_ginsim_object(data):
                        biolqm = import_colomoto_tool("biolqm")
                        imported = biolqm_import(biolqm, ginsim.to_biolqm(data))
                if not imported:
                    self.import_data(data)
        for a, f in kwargs.items():
            self[a] = f

    @classmethod
    def auto_cast(celf, obj):
        if isinstance(obj, celf):
            return obj
        return celf(obj)

    def import_data(self, data):
        raise NotImplementedError
    def source(self, sep):
        raise NotImplementedError
    def __repr__(self):
        return self.source(sep=" <- ")

    @classmethod
    def load(celf, filename, **kwargs):
        f = celf(**kwargs)
        filename = ensure_localfile(filename)
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
            if isinstance(v, str):
                v = self.ba.parse(v)
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
        return {a: _autostate(self[a].subs(tr).simplify()) for a in self}

    def zero(self):
        return {a:0 for a in self}

    def rewrite(self, a, tr, simplify=True):
        tr = self._normalize_tr(tr)
        self[a] = self[a].subs(tr, simplify=simplify)

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

    def _quick_rename(self, name, newname):
        if newname == name:
            return
        assert newname not in self, "Node {} already exists!".format(newname)
        self[newname] = self[name]
        del self[name]

    def rename(self, a, b):
        self._quick_rename(a, b)
        for n in self:
            self.rewrite(n, {a:b}, simplify=False)

    def sanitize_names(self):
        def _sanitize_name(name):
            sname = unicodedata.normalize("NFD", name)
            sname = re_nonword.sub("_", sname)
            if sname != name:
                basesname = sname
                tag = 2
                while sname in self:
                    sname = f"{basesname}_{tag}"
                    tag += 1
                self._quick_rename(name, sname)
                return sname

        names = list(sorted(self.keys()))
        tr = {}
        btr = {}
        for name in names:
            sname = _sanitize_name(name)
            if sname:
                tr[name] = sname
                btr[self.v(name)] = self.v(sname)
        if btr:
            for a in self:
                self.rewrite(a, btr, simplify=False)
        return tr

    biolqm_format = None
    def to_biolqm(self):
        bnfile = new_output_file(ext=self.biolqm_format)
        with open(bnfile, "w") as f:
            f.write(self.source())
        biolqm = import_colomoto_tool("biolqm")
        return biolqm.load(bnfile)


def simplify_dnf(ba, f):
    def is_wellformed_dnf(f):
        pos, neg = set(), set()
        def is_lit(f):
            if isinstance(f, ba.Symbol):
                pos.add(f.obj)
                return True
            elif isinstance(f, ba.NOT) \
                    and isinstance(f.args[0], ba.Symbol):
                neg.add(f.args[0].obj)
                return True
            return False

        def is_clause(f):
            if is_lit(f):
                return True
            if isinstance(f, ba.AND):
                for g in f.args:
                    if not is_lit(g):
                        return False
                return True
            return False

        if f is ba.TRUE or f is ba.FALSE:
            return True, set()
        if is_clause(f):
            return True, pos.intersection(neg)
        if isinstance(f, ba.OR):
            for g in f.args:
                if not is_clause(g):
                    return False, None
            return True, pos.intersection(neg)
        return False, None

    is_dnf, suspects = is_wellformed_dnf(f)
    if is_dnf and suspects:
        return ba.dnf(ba.cnf(f))
    return f

def struct_of_dnf(ba, f, container=frozenset, sort=False):
    def make_lit(l):
        if isinstance(l, ba.NOT):
            return (l.args[0].obj, False)
        else:
            return (l.obj, True)
    def make_clause(c):
        if isinstance(c, ba.AND):
            lits = c.args
        else:
            lits = [c]
        lits = map(make_lit, lits)
        return container(sorted(lits) if sort else lits)
    if f is ba.TRUE:
        return True
    elif f is ba.FALSE:
        return False
    if not isinstance(f, ba.OR):
        clauses = [f]
    else:
        clauses = f.args
    clauses = map(make_clause, clauses)
    return container(sorted(clauses) if sort else clauses)

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
            line = line.split("#")[0].strip()
            if not line:
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
            f = f.simplify()
            f = simplify_dnf(self.ba, f)
            bn[a] = f
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
        return {i: make_dnf(f) for (i,f) in self.items()}

    def make_hash(self, simplify=False):
        """
        compute a hash for the BN based on its DNF representation
        """
        D = []
        for i, f in sorted(self.items()):
            if f not in [self.ba.TRUE, self.ba.FALSE]:
                f = self.ba.dnf(f)
                if simplify:
                    f = simplify_dnf(self.ba, f)
            struct = struct_of_dnf(self.ba, f, container=tuple, sort=True)
            D.append((i,struct))
        return hashlib.md5(str(D).encode()).hexdigest()

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

    def constants(self):
        csttypes = [boolean.boolean._TRUE, boolean.boolean._FALSE]
        return {i:f is self.ba.TRUE for i,f in self.items() \
                if type(f) in csttypes}

    def propagate_constants(self):
        csttypes = [boolean.boolean._TRUE, boolean.boolean._FALSE]
        bn = self.copy()
        csts = {i:f for i, f in bn.items() if type(f) in csttypes}
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

    def to_pyboolnet(self):
        PyBoolNet = import_colomoto_tool("PyBoolNet")
        fd, bnetfile = tempfile.mkstemp(".bnet")
        try:
            with os.fdopen(fd, "w") as fp:
                fp.write(self.source())
            return PyBoolNet.FileExchange.bnet2primes(bnetfile)
        finally:
            os.unlink(bnetfile)

    def dynamics(self, update_mode="asynchronous", init=None, loops=None):
        """
        Returns a directed graph (`networkx.DiGraph` object) of the dynamics
        with the `update_mode`.

        :param update_mode: either `"asynchronous"` (or equivalently
            `"fully-asynchronous"`), `"synchronous"` (or equivalently
            `"parallel"`), `"general"`.
            Alternatively, it can be a function returning an
            :class:`.UpdateModeDynamics` object.
        :param dict[str,int] init: Optional initial state from which the
            dynamics is computed.
        """
        if isinstance(update_mode, str):
            if update_mode in ["asynchronous", "fully-asynchronous"]:
                update_mode = FullyAsynchronousDynamics
            elif update_mode == "general":
                update_mode = GeneralAsynchronousDynamics
            elif update_mode in ["synchronous", "parallel"]:
                update_mode = SynchronousDynamics
            else:
                raise ValueError(f"Unknown update mode {update_mode}")
        opts = {}
        if loops is not None:
            opts["loops"] = loops
        update_mode = update_mode(self, **opts)
        if init:
            return update_mode.partial_dynamics(init)
        else:
            return update_mode.dynamics()

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
        return False
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

    def simplify(self):
        mn = copy.copy(self)
        for a, spec in self.items():
            if isinstance(spec, dict):
                mn[a] = {i: f.simplify() for i,f in spec.items()}
            elif isinstance(spec, boolean.Expression):
                mn[a] = spec.simplify()
            else: # list
                mn[a] = [(i,f.simplify()) for i,f in spec]
        return mn

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

    def influence_graph(self):
        import networkx as nx
        influences = set()
        ig = nx.MultiDiGraph()
        for a, f in self.items():
            ig.add_node(a)
            for d, spec in self._normalize(a, f):
                for lit in spec.simplify().literalize().get_literals():
                    if isinstance(lit, boolean.NOT):
                        b = lit.args[0]
                        sign = -1
                    else:
                        b = lit
                        sign = 1
                    b = self._autokey(b.nodevar())
                    influences.add((b,a,sign))
        for (b, a, sign) in influences:
            ig.add_edge(b, a, sign=sign, label="+" if sign > 0 else "-")
        return ig


class _Run(object):
    def __init__(self, model, init, k):
        """
        Run at most `k` steps of an execution of given `model` from initial
        configuration `init`.

        Stops at fixpoints.
        """
        if not isinstance(model, BooleanNetwork):
            raise TypeError("Only BooleanNetwork objects are supported")
        self.model = model
        self.init = init
        self.k = k
    def select_for_update(self, nodes):
        """
        Return the sub-sequence of `nodes` to actually update
        """
        raise NotImplementedError
    def __iter__(self):
        cur = self.init.copy()
        yield cur.copy()
        for i in range(self.k):
            target = self.model(cur)
            update = [a for a,i in target.items() if cur[a] != i]
            if not update:
                return
            update = self.select_for_update(update)
            for a in update:
                cur[a] = target[a]
            yield cur.copy()

class _RandomRun(_Run):
    def __init__(self, model, init, k, seed=None):
        super().__init__(model, init, k)
        self.random = random.Random(seed)

class SyncRun(_Run):
    """
    Synchronous update run
    """
    def select_for_update(self, nodes):
        return nodes
class FAsyncRun(_RandomRun):
    """
    Fully-asynchronous update run
    """
    def select_for_update(self, nodes):
        return (self.random.choice(nodes),)
class GAsyncRun(_RandomRun):
    """
    (General) asynchronous update run
    """
    def select_for_update(self, nodes):
        k = len(nodes)
        mask = 0
        while not mask:
            mask = self.random.getrandbits(k)
        mask = "{0:b}".format(mask).rjust(k, "0")
        return [a for (a,sel) in zip(nodes, mask) if sel == "1"]


class UpdateModeDynamics(object):
    """
    Abstract class for the updating mode of a BooleanNetwork object
    """
    def __init__(self, model, loops=False):
        if not isinstance(model, BooleanNetwork):
            raise TypeError("Only BooleanNetwork objects are supported")
        self.model = model
        self.nodes = tuple(model)
        self.n = len(self.nodes)
        self.loops = loops

    def __call__(self, x):
        """
        Sub-classes have to implement this method which should return an
        iterator (or list) over the states following `x`.
        """
        raise NotImplementedError

    def push(self, d, x):
        def fmt(z):
            return "".join([str(z[i]) for i in self.nodes])
        rx = fmt(x)
        d.add_node(rx)
        children = list(self(x))
        for y in children:
            ry = fmt(y)
            if rx != ry or self.loops:
                d.add_edge(rx, ry)
        return children

    def random_walk(self, init, steps=0, stop_condition=None, stop_at=None):
        if stop_at:
            stop_at = HypercubeCollection.cast(stop_at)
            user_stop = stop_condition
            def stop_condition(x):
                if user_stop is not None and user_stop(x):
                    return True
                return stop_at.match_state(x)

        x = init
        yield x
        i = 0
        while True:
            i += 1
            nexts = list(self(x))
            if not nexts or (len(nexts) == 1 and nexts[0] == x):
                return
            x = random.choice(nexts)
            yield x
            if i == steps:
                break
            if stop_condition is not None and stop_condition(x):
                break

    def dynamics(self):
        d = nx.DiGraph()
        x = {i: 0 for i in self.nodes}
        self.push(d, x)
        even = True
        right = -1
        for m in range(1,2**self.n):
            if even:
                x[self.nodes[0]] = 1-x[self.nodes[0]]
                for i in range(self.n):
                    if x[self.nodes[i]]:
                        right = i
                        break
            else:
                x[self.nodes[right+1]] = 1-x[self.nodes[right+1]]
                if x[self.nodes[right+1]]:
                    right = right+1
            even = not even
            self.push(d, x)
        return d

    def partial_dynamics(self, init):
        d = nx.DiGraph()
        def m(x):
            return tuple([x[i] for i in self.nodes])
        init = {i: int(init[i]) for i in self.nodes}
        todo = {m(init)}
        done = set()
        while todo:
            mx = todo.pop()
            x = dict(zip(self.nodes, mx))
            done.add(mx)
            for y in self.push(d, x):
                my = m(y)
                if my not in done:
                    todo.add(my)
        return d

class ElementaryUpdateModeDynamics(UpdateModeDynamics):
    def __init__(self, model, min_u, max_u, **opts):
        super().__init__(model, **opts)
        self.min_u = min_u
        self.max_u = max_u

    def __call__(self, x):
        z = self.model(x)
        for k in range(self.min_u, self.max_u+1):
            for I in itertools.combinations(self.nodes, k):
                y = x.copy()
                mod = False or self.loops
                for i in I:
                    if z[i] != y[i]:
                        mod = True
                    y[i] = z[i]
                if mod:
                    yield y

class FullyAsynchronousDynamics(ElementaryUpdateModeDynamics):
    def __init__(self, model, **opts):
        super().__init__(model, 1, 1, **opts)
class GeneralAsynchronousDynamics(ElementaryUpdateModeDynamics):
    def __init__(self, model, **opts):
        n = len(model)
        super().__init__(model, 1, n, **opts)
class SynchronousDynamics(ElementaryUpdateModeDynamics):
    def __init__(self, model, loops=True, **opts):
        n = len(model)
        super().__init__(model, n, n, loops=loops, **opts)
ParallelDynamics = SynchronousDynamics

class PeriodicDynamics(UpdateModeDynamics):
    """
    Periodic (deterministic) updating mode.

    It is parameterized by a sequence of sets of nodes to update simultaneously
    in order to compute the next configuration.

    """
    def __init__(self, sequence, model, loops=True):
        super().__init__(model, loops=loops)
        # allow for elements of the sequence to be directly a node
        def magic(I):
            if isinstance(I, Hashable) and I in model:
                return {I}
            return I
        self.sequence = tuple(map(magic, sequence))

    def __call__(self, x):
        y = x.copy()
        for I in self.sequence:
            z = self.model(y)
            for i in I:
                y[i] = z[i]
        yield y

class BlockSequentialDynamics(PeriodicDynamics):
    pass

class SequentialDynamics(BlockSequentialDynamics):
    def __init__(self, sequence, model, **opts):
        super().__init__([(i,) for i in sequence], model, **opts)


class BlockParallelDynamics(BlockSequentialDynamics):
    def __init__(self, spec, model, **opts):
        def magic(I):
            if isinstance(I, Hashable) and I in model:
                return (I,)
            return I
        spec = [magic(I) for I in spec]
        l = max(map(len,spec))
        def m(seq):
            ls = len(seq)
            return l//ls + (1 if l%ls else 0)
        spec = [seq*m(seq) for seq in spec]
        sequence = [{seq[i] for seq in spec if seq[i] is not None} \
                for i in range(l)]
        super().__init__(sequence, model, **opts)
