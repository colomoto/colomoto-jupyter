
class LogicOperator(object):
    def __and__(l, r):
        return And(l, r)
    def __or__(l, r):
        return Or(l, r)
    def __invert__(a):
        return Not(a)

class UnaryOperator(LogicOperator):
    def __init__(self, a):
        self.arg = a
    def __str__(self):
        return "{} ({})".format(self.__class__.__name__, self.arg)
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__,
            repr(self.arg))

class BinaryOperator(LogicOperator):
    def __init__(self, l, r):
        self.left = l
        self.right = r
    def __repr__(self):
        return "{}({},{})".format(self.__class__.__name__,
            repr(self.left), repr(self.right))

class And(BinaryOperator):
    def __str__(self):
        return "({}) & ({})".format(self.left, self.right)
class Or(BinaryOperator):
    def __str__(self):
        return "({}) | ({})".format(self.left, self.right)
class Not(UnaryOperator):
    def __str__(self):
        return "!({})".format(self.arg)
class If(BinaryOperator):
    def __str__(self):
        return "({}) -> ({})".format(self.left, self.right)

class State(UnaryOperator):
    def __str__(self):
        return self.arg

from colomoto import ModelState

def colomoto_state_cls(tr):
    class ColomotoState(UnaryOperator):
        def __init__(self, *args, **kwargs):
            state = ModelState(*args, **kwargs)
            arg = frozenset([tr(ai) for ai in state.items()])
            UnaryOperator.__init__(self, arg)
        def __str__(self):
            return " & ".join(self.arg)
    return ColomotoState

##
# LTL
##
class F(UnaryOperator):
    pass
class G(UnaryOperator):
    pass
class U(BinaryOperator):
    pass

##
# CTL
##
class EF(UnaryOperator):
    pass
class EG(UnaryOperator):
    pass
class EU(BinaryOperator):
    def __str__(self):
        return "E (({}) U ({}))".format(self.left, self.right)
class AF(UnaryOperator):
    pass
class AG(UnaryOperator):
    pass
class AU(BinaryOperator):
    def __str__(self):
        return "A (({}) U ({}))".format(self.left, self.right)

__all__ = ["If", "State",
    "colomoto_state_cls",
    "F", "G", "U",
    "EF", "AF", "EG", "AG", "EU", "AU"]

