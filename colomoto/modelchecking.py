
from .temporal_logics import nusmv_of_expr

from nusmv import NuSMV

def default_state_tr(ai):
    return "{}={}".format(*ai)

class ColomotoNuSMV(NuSMV):
    def __init__(self, filename, tr=default_state_tr):
        NuSMV.__init__(self, filename)
        self.tr = tr

    def add_spec(self, tspec, expr, **kwargs):
        expr = nusmv_of_expr(expr, self.tr)
        super(ColomotoNuSMV, self).add_spec(tspec, expr, **kwargs)


