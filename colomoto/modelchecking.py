
from .temporal_logics import colomoto_state_cls

from nusmv import NuSMV

def default_state_tr(ai):
    return "{}={}".format(*ai)

class ColomotoNuSMV(NuSMV):
    def __init__(self, filename, tr=default_state_tr):
        NuSMV.__init__(self, filename)
        self.S = colomoto_state_cls(tr)


