import unittest

from colomoto import minibn

def bn1():
    return minibn.BooleanNetwork({
            "a": "b",
            "b": "a|b"
        })

class TestConversions(unittest.TestCase):
    def test_pyboolnet(self):
        bn = bn1()
        pybn = bn.to_pyboolnet()
