from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from numbers import Number
import operator
from typing import Any


def evaluate(form: Formula | Term):
    """Given a Term or Formula get the *current* value it contains. For terms
    this is the same as .unwrap() method, but for for Formula, the entire
    expression is recursively evaluated.

    :param form: A formula (or term) to extract the current value of.
    :type form: class: Formula | Term
    :return: The *current* value of the Formula or Term.
    """
    # Basic building blocks are variables and constants (i.e. Terms)
    if isinstance(form, Term):
        return form.unwrap()
    else: # Otherwise, recursively evaluate.
        # Either formula f(smaller_formula) or small_formula x small_formula2
        if form.bin_op is None:
            return form.unary_op(evaluate(form._rhs))
        else:
            return form.bin_op(
                    evaluate(form._lhs), 
                    evaluate(form._rhs)
                )

# String representation for unary and binary operations. Used in __str__ for
# a Formula

__bin_str_map = {
    # Arithmetic operators.
    operator.add : '+',
    operator.mul : '*',
    operator.sub : '-',
    operator.truediv : '/',
    operator.floordiv : '//',
    operator.xor : '^',
    # Comparison operators.
    operator.lt : '<',
    operator.le : '<=',
    operator.eq : '==',
    operator.ne : '!=',
    operator.ge : '>=',
    operator.gt : '>'
}


__unary_str_map = {
    operator.abs : 'abs',
    operator.not_ : 'not',
    operator.pos : '+',
    operator.neg : '-',
}


# Similar to here https://stackoverflow.com/a/7844038/667648
def _register_bin_op(bin_op):
    """Helper function intended to help construct binary operations (like 
    __add__) for Formula and Term."""
    def b(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=bin_op, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula
    return b

def _register_rbin_op(bin_op):
    """Helper function intended to help construct binary operations (like 
    __radd__) for Formula and Term."""
    def b(self, other):
        if isinstance(other, Number):
            other = Term(other)
        # Order of params are switched for the r version!
        formula = Formula(bin_op=bin_op, _lhs=other, _rhs=self)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula
    return b

def _register_unary_op(unary_op):
    """Helper function inteded to help construct unary operations (like
    __abs__) for Formula and Term."""
    def u(self):
        formula = Formula(unary_op=unary_op, _rhs=self)
        self._parents.append(formula)
        return formula
    return u 

@dataclass
class Formula:
    """A Well-Formed-Formula that consists of Term objects (i.e. variables) and 
    operators."""
    unary_op: Callable[[Any], Any] = None
    _lhs: Formula = None,
    bin_op: Callable[[Any, Any], Any] = None 
    _rhs: Formula = None
    _parents: list[Formula] = field(default_factory=list)
    _binds: Any = field(default_factory=list)
    _fire_on: list[Callable] = field(default_factory=list)

    def _update(self):
        self._value = evaluate(self)
        for parent in self._parents:
            parent._update()
        for obj, field_name in self._binds:
            setattr(obj, field_name, self._value)
        for func in self._fire_on:
            if self.unwrap(): # If the value has True truthiness, call the 
                 func()       # function.

    def unwrap(self):
        """Get the value the formula currently evaluates to."""
        return evaluate(self)

    def __str__(self):
        global __bin_str_map
        global __unary_str_map
        if not self.bin_op:
            return __unary_str_map[self.unary_op] + " (" + str(self._rhs) + ")"
        return f"({str(self._lhs)}) {__bin_str_map[self.bin_op]} ({str(self._rhs)})"

    # Binary operations
    __add__ = _register_bin_op(operator.add)
    __radd__ = _register_rbin_op(operator.add)
    __mul__ = _register_bin_op(operator.mul)
    __rmul__ = _register_rbin_op(operator.mul)
    __truediv__ = _register_bin_op(operator.truediv)
    __rtruediv__ = _register_rbin_op(operator.truediv)
    __floordiv__ = _register_bin_op(operator.floordiv)
    __rfloordiv__ = _register_rbin_op(operator.floordiv)
    __xor__ = _register_bin_op(operator.xor)
    __rxor__ = _register_rbin_op(operator.xor)

    # Unary operations
    __abs__ = _register_unary_op(operator.abs)
    __not__ = _register_unary_op(operator.not_)
    __pos__ = _register_unary_op(operator.pos)
    __neg__ = _register_unary_op(operator.neg)


def _register_ibin_op(bin_op):
    """Helper function intended to help construct binary operations (like 
    __radd__) for Formula and Term."""
    def b(self, other):
        self._value = bin_op(self._value, other)
        self._propegate()
        return self
    return b


@dataclass
class Term:
    """Essentially a variable that may be updated by the user. Can be included
    in more complicated formula and whenever it is changed, the parent formula
    are also updated to reflect this change."""
    _value: Any = None
    # Parent formulas containing the variable.
    _parents: list[Formula] = field(default_factory=list)
    # Raw Python fields that should change on update of this Term.
    _binds: list[(Any, Any)] = field(default_factory=list)
    # List of functions that are executed if this Term is True.
    _fire_on: Callable = field(default_factory=list)

    def _propegate(self):
        for parent in self._parents:
            parent._update()
        # Even a lonesome Term may be bound to a field.
        for obj, field_name in self._binds:
            setattr(obj, field_name, self._value)
        # or it may also be given a contract.
        for func in self._fire_on:
            if self.unwrap():
                func()

    def change(self, new_value):
        """Change the wrapped value of the term. (Internally updates formulas
        that use this term.)
        
        :param new_value: The value to change self.value to.
        """
        # Nothing actually changed.
        if self._value == new_value:
            return
        # Something did change.
        self._value = new_value
        self._propegate()

    def unwrap(self):
        return self._value

    def __str__(self):
        return f"Term({self._value})"

    # Binary operators
    __add__ = _register_bin_op(operator.add)
    __radd__ = _register_rbin_op(operator.add)
    __mul__ = _register_bin_op(operator.mul)
    __rmul__ = _register_rbin_op(operator.mul)
    __truediv__ = _register_bin_op(operator.truediv)
    __rtruediv__ = _register_rbin_op(operator.truediv)
    __floordiv__ = _register_bin_op(operator.floordiv)
    __rfloordiv__ = _register_rbin_op(operator.floordiv)
    __xor__ = _register_bin_op(operator.xor)
    __rxor__ = _register_rbin_op(operator.xor)

    # Unary operators
    __abs__ = _register_unary_op(operator.abs)
    __not__ = _register_unary_op(operator.not_)
    __pos__ = _register_unary_op(operator.pos)
    __neg__ = _register_unary_op(operator.neg)
    
    # Comparison operators. 
    __lt__ = _register_bin_op(operator.lt)
    __rlt__ = _register_rbin_op(operator.lt)
    __gt__ = _register_bin_op(operator.gt)
    __rgt__ = _register_rbin_op(operator.gt)
    __ge__ = _register_bin_op(operator.ge)
    __rge__ = _register_rbin_op(operator.ge)
    __eq__ = _register_bin_op(operator.eq)
    __req__ = _register_rbin_op(operator.eq)
    __ne__ = _register_bin_op(operator.ne)
    __rne__ = _register_rbin_op(operator.ne)    

    # In place assignment. NOTE: Although something like a += 1 should be the 
    # same as a = a + 1, it is *not* in this library. a += 1 changes increments
    # the term. a = a + 1 makes a become the formula a + 1.
    
    __iadd__ = _register_ibin_op(operator.iadd)
    __iand__ = _register_ibin_op(operator.iand)
    __itruediv__ = _register_ibin_op(operator.itruediv)
    __ifloordiv__ = _register_ibin_op(operator.ifloordiv)
    __ilshift__ = _register_ibin_op(operator.ilshift)
    __irshift__ = _register_ibin_op(operator.irshift)
    __imod__ = _register_ibin_op(operator.imod)
    __imul__ = _register_ibin_op(operator.imul)
    __imatmul__ = _register_ibin_op(operator.imatmul)
    __ior__ = _register_ibin_op(operator.ior)
    __ipow__ = _register_ibin_op(operator.ipow)
    __isub__ = _register_ibin_op(operator.isub)
    __ixor__ = _register_ibin_op(operator.ixor)


def bind(obj, field_name, form):
    """Given an object and a field name, you can "bind" it to a Formula (or 
    Term). That is, whenever the Formula (or Term) is updated, the field for
    the object is also updated.

    :param obj: The object to update.
    :param field_name: The field specific field of `obj` to change.
    :param form: A Formula or Term that `obj.field` is updated to be equivalent
        to.
    """
    form._binds.append((obj, field_name))

def fire_on(form):
    """Use as a decorator: If a Formula's truthiness is True, call the
    decorated function.

    :param form: Execute the proceeding function if `form` evaluates to True at
        some point in time.
    """
    def fire_decorator(func):
        form._fire_on.append(func)
        return func
    return fire_decorator
