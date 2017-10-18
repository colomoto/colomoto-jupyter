
import sys

from ginsim.gateway import japi, restart

class BioLQM(object):
    def restart(self):
        restart()

    def __getattr__(self, name):
        return getattr(japi.lqm, name)

sys.modules[__name__] = BioLQM()


