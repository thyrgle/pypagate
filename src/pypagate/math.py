import math as _math
from numbers import Number
from pypagate import Formula, Term

def _reactive_unary(func):
    """Wraps standard math functions to return reactive Formulas."""
    def wrapper(x):
        # If the user passes a raw number, wrap it in a Term to maintain graph integrity.
        if isinstance(x, Number):
            x = Term(x)
        # Generate the reactive node
        formula = Formula(unary_op=func, _rhs=x)
        # Bind the node to the parent to ensure signal propagation
        x._parents.append(formula)
        return formula
    return wrapper

# Expose standard trigonometric and algebraic functions
acos = _reactive_unary(_math.acos)
asin = _reactive_unary(_math.asin)
atan = _reactive_unary(_math.atan)
cos = _reactive_unary(_math.cos)
sin = _reactive_unary(_math.sin)
tan = _reactive_unary(_math.tan)
exp = _reactive_unary(_math.exp)
log = _reactive_unary(_math.log)
log10 = _reactive_unary(_math.log10)
sqrt = _reactive_unary(_math.sqrt)