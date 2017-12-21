
from colomoto import ModelState

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
    pass
class Or(BinaryOperator):
    pass
class Not(UnaryOperator):
    pass
class If(BinaryOperator):
    pass

class S(UnaryOperator):
    def __init__(self, arg=None, **kwargs):
        assert arg or kwargs, "S must have an argument"
        if arg:
            assert not kwargs, "Cannot mix arg with kwargs"
            self.arg = arg
        elif kwargs:
            self.arg = ModelState(**kwargs)

##
# LTL
##
class X(UnaryOperator):
    pass
class F(UnaryOperator):
    pass
class G(UnaryOperator):
    pass
class U(BinaryOperator):
    pass

##
# CTL
##
class EX(UnaryOperator):
    pass
class EF(UnaryOperator):
    pass
class EG(UnaryOperator):
    pass
class EU(BinaryOperator):
    pass
class AX(UnaryOperator):
    pass
class AF(UnaryOperator):
    pass
class AG(UnaryOperator):
    pass
class AU(BinaryOperator):
    pass

def nusmv_of_expr(e, tr):
    def to_nusmv(e):
        op = e.__class__.__name__
        if isinstance(e, str):
            return e
        elif isinstance(e, (ModelState, dict)):
            def nusmv_of_ai(ai):
                a, i = ai
                if isinstance(i, (tuple, set, list)):
                    return "({})".format(" | ".join([tr((a,j)) for j in i]))
                else:
                    return tr(ai)
            return " & ".join(map(nusmv_of_ai, e.items()))
        elif isinstance(e, UnaryOperator):
            arg = to_nusmv(e.arg)
            if isinstance(e, Not):
                return "!({})".format(arg)
            elif isinstance(e, S):
                return arg
            else:
                return "{} ({})".format(op, arg)
        elif isinstance(e, BinaryOperator):
            right = to_nusmv(e.right)
            left = to_nusmv(e.left)
            if isinstance(e, And):
                tmpl = "({}) & ({})"
            elif isinstance(e, Or):
                tmpl = "({}) | ({})"
            elif isinstance(e, If):
                tmpl = "({}) -> ({})"
            elif isinstance(e, EU):
                tmpl = "E (({}) U ({}))"
            elif isinstance(e, AU):
                tmpl = "A (({}) U ({}))"
            return tmpl.format(left, right)
        else:
            raise NotImplementedError
    return to_nusmv(e)


__all__ = ["If", "S", "ModelState",
    "F", "G", "U",
    "EF", "AF", "EG", "AG", "EU", "AU",
    "nusmv_of_expr"]

