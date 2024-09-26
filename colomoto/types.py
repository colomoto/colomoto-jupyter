
import logging
import os
import subprocess
import tempfile

import pandas as pd

def multivalue_merge(a,b):
    if a == b:
        return a
    if a == "*" or b == "*":
        return "*"
    mv = set()
    for x in [a,b]:
        if isinstance(x,int):
            mv.add(x)
        else:
            mv.update(x)
    return tuple(mv)

class PartialState(dict):
    def match_state(self, s):
        for k, v in self.items():
            if v != "*" and s[k] != v:
                return False
        return True
    match_partial_state = match_state
    def project(self, keys):
        return dict([(k,v) for k,v in self.items() if k in keys])

    def as_dataframe(self):
        return pd.DataFrame([self])

class State(PartialState):
    def count(self):
        """
        Returns number of states represented by this object (1)
        """
        return 1
    def simplify(self):
        return self

class Hypercube(dict):
    def extend(self, ts):
        if not isinstance(ts, Hypercube):
            ts = Hypercube(ts)
        return HypercubeCollection([self, ts])
    def match_partial_state(self, ps):
        for k, v in ps.items():
            av = self.get(k)
            if av != "*" and av != v:
                return False
        return True
    match_state = match_partial_state

    def project(self, keys):
        return dict([(k,v) for k,v in self.items() if k in keys])

    def count(self):
        """
        Returns number of states represented by this object
        """
        return 2**len([v for v in self.values() if not isinstance(v,int)])

    def simplify(self):
        """
        Returns a :py:class:`.State` object if there is no free component in
        this hypercube, *self* otherwise.
        """
        if self.is_single_state:
            return State(self)
        return self

    def as_dataframe(self):
        return pd.DataFrame([self])

    @property
    def is_single_state(self):
        for v in self.values():
            if not isinstance(v,int):
                return False
        return True

class HypercubeCollection(list):
    def extend(self, ts):
        if not isinstance(ts, Hypercube):
            ts = Hypercube(ts)
        return self.__class__(self+[ts])
    def match_partial_state(self, ps):
        for tsa in self:
            if tsa.match_partial_state(ps):
                return True
        return False
    match_state = match_partial_state

    def project(self, keys):
        p = self[0].project(keys)
        for tp in self[1:]:
            for k,v in tp.project(keys).items():
                p[k] = multivalue_merge(p[k], v)
        return p

    def count(self):
        """
        Returns number of states represented by this object
        """
        return sum([h.count() for h in self])

    def simplify(self):
        """
        Warning: supports only Boolean states
        """
        if len(self) == 1:
            return self[0].simplify()

        try:
            subprocess.run(["espresso", "-h"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            logging.warning("The espresso tool is not installed, skipping simplification.\nConsider executing `python -m espresso_setup`.")
            return self

        nodes = list(self[0])

        fd, inp = tempfile.mkstemp(prefix="colomoto-espresso")
        try:
            with os.fdopen(fd, "w") as fp:
                fp.write(f".i {len(nodes)}\n.o 1\n")
                for h in self:
                    fp.write("".join([str(h[n]).replace("*","-") for n in nodes]))
                    fp.write(" 1\n")
                fp.write(".type f\n")
                fp.write(".e\n")
            esp = subprocess.run(["espresso", inp], capture_output=True,
                    encoding="ascii")
            if esp.returncode == 0:
                hs = [dict(zip(nodes, list(l.split(" ")[0].replace("-", "*"))))
                        for l in esp.stdout.split("\n")[3:-2]]
                hs = [Hypercube(h).simplify() for h in hs]
                if len(hs) > 1:
                    return self.__class__(hs)
                else:
                    return hs[0]
        finally:
            os.unlink(inp)

        return self

    def as_dataframe(self):
        return pd.DataFrame(self)

    @property
    def is_single_state(self):
        return False

    @classmethod
    def cast(celf, states):
        if isinstance(states, (celf, Hypercube, PartialState)):
            return states
        if isinstance(states, dict):
            vals = set(states.values())
            if "*" in vals:
                return Hypercube(states)
            if vals.difference([0,1]):
                raise NotImplementedError("Use '*' to indicate free values")
            return PartialState(states)
        if isinstance(states, list):
            return celf([celf.cast(s) for s in states])
        raise TypeError(f"Don't know how to cast {type(states)}")

# Deprecated
class TrapSpaceAttractor(Hypercube):
    pass
class TrapSpacesAttractor(HypercubeCollection):
    pass
