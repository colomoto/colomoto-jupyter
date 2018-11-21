
from .temporal_logics import nusmv_of_expr, its_of_expr

from nusmv import NuSMV
from itstools import ITSModel

def default_state_tr(ai):
    return "{}={}".format(*ai)

class ColomotoNuSMV(NuSMV):
    def __init__(self, filename, tr=default_state_tr):
        NuSMV.__init__(self, filename)
        self.tr = tr

    def add_spec(self, tspec, expr, **kwargs):
        expr = nusmv_of_expr(expr, self.tr)
        super(ColomotoNuSMV, self).add_spec(tspec, expr, **kwargs)

class ColomotoITS(ITSModel):
    def __init__(self, filename, tr=default_state_tr, **kwargs):
        ITSModel.__init__(self, filename, **kwargs)
        self.tr = tr

    def reachability(self, state_formula, **kwargs):
        state_formula = its_of_expr(state_formula, self.tr)
        return super(ColomotoITS, self).reachability(state_formula, **kwargs)

    def verify_ctls(self, specs, **kwargs):
        if isinstance(specs, dict):
            for k in specs:
                specs[k] = its_of_expr(specs[k], self.tr)
        else:
            specs = [its_of_expr(ctl, self.tr) for ctl in specs]
        return super(ColomotoITS, self).verify_ctls(specs, **kwargs)

