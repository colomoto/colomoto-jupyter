
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
    def project(self, keys):
        return dict([(k,v) for k,v in self.items() if k in keys])

class State(PartialState):
    pass

class TrapSpaceAttractor(dict):
    def extend(self, ts):
        if not isinstance(ts, TrapSpaceAttractor):
            ts = TrapSpaceAttractor(ts)
        return TrapSpacesAttractor([self, ts])
    def match_partial_state(self, ps):
        for k, v in ps.items():
            av = self.get(k)
            if av != "*" and av != v:
                return False
        return True
    def project(self, keys):
        return dict([(k,v) for k,v in self.items() if k in keys])

    @property
    def is_single_state(self):
        for v in self.values():
            if not isinstance(v,int):
                return False
        return True

class TrapSpacesAttractor(list):
    def extend(self, ts):
        if not isinstance(ts, TrapSpaceAttractor):
            ts = TrapSpaceAttractor(ts)
        return TrapSpacesAttractor(self+[ts])
    def match_partial_state(self, ps):
        for tsa in self:
            if tsa.match_partial_state(ps):
                return True
        return False
    def project(self, keys):
        p = self[0].projec(keys)
        for tp in self[1:]:
            for k,v in tp.project(keys).items():
                p[k] = multivalue_merge(p[k], v)
        return p

    @property
    def is_single_state(self):
        return False

