from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from numbers import Number
import operator
from typing import Any


def evaluate(form: Formula | Term):
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


@dataclass
class Formula:
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
        if not self.bin_op:
            return __unary_str_map[self.unary_op] + " " + str(self._rhs)
        return str(self._lhs) + " " \
             + __bin_str_map[self.bin_op] + " " \
             + str(self._rhs)

    # Binary operations
    def __add__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.add, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __radd__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.add, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __mul__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.mul, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __rmul__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.mul, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __truediv__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.truediv, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __rtruediv__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.truediv, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __floordiv__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.floordiv, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __rfloordiv__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.floordiv, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __xor__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.xor, _lhs=self, _rhs=other)
        other._parents.append(formula)
        return formula

    def __rxor__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.xor, _lhs=self, _rhs=other)
        other._parents.append(formula)
        return formula

    # Unary operations
    def __abs__(self):
        formula = Formula(unary_op=operator.abs, _rhs=self)
        return formula


@dataclass
class Term:
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
    def __add__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.add, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __radd__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.add, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __mul__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.mul, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __rmul__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.mul, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __truediv__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.truediv, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __rtruediv__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.truediv, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __floordiv__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.floordiv, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __xor__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.xor, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    # Unary operators
    def __abs__(self):
        formula = Formula(unary_op=operator.abs, _rhs=self)
        self._parents.append(formula)
        return formula

    def __not__(self):
        formula = Formula(unary_op=operator.not_, _rhs=self)
        self._parents.append(formula)
        return formula

    def __pos__(self):
        formula = Formula(unary_op=operator.pos, _rhs=self)
        self._parents.append(formula)
        return formula
    
    def __neg__(self):
        formula = Formula(unary_op=operator.neg, _rhs=self)
        self._parents.append(formula)
        return formula

    # Comparison operators. 
    def __lt__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.lt, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __rlt__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.lt, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __gt__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.gt, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __rgt__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.gt, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __ge__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.ge, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __rge__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.ge, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __eq__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.eq, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __req__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.eq, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
    
    def __ne__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.eq, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    def __rne__(self, other):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=operator.eq, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula

    # In place assignment. NOTE: Although something like a += 1 should be the 
    # same as a = a + 1, it is *not* in this library. a += 1 changes increments
    # the term. a = a + 1 makes a become the formula a + 1.
    
    def __iadd__(self, other):
        self._value += other
        self._propegate()
        return self

    def __iand__(self, other):
        self._value &= other
        self._propegate()
        return self

    def __ifloordiv(self, other):
        self._value //= other
        self._propegate()
        return self

    def __ilshift__(self, other):
        self._value <<= other
        self._propegate()
        return self

    def __imod__(self, other):
        self._value %= other
        self._propegate()
        return self

    def __imul__(self, other):
        self._value *= other
        self._propegate()
        return self

    def __imatmul__(self, other):
        self._value @= other
        self._propegate()
        return self

    def __ior__(self, other):
        self._value |= other
        self._propegate()
        return self

    def __ipow__(self, other):
        self._value |= other
        self._propegate()
        return self

    def __irshift__(self, other):
        self._value >>= other
        self._propegate()
        return self

    def __isub__(self, other):
        self._value -= other
        self._propegate()
        return self

    def __itruediv__(self, other):
        self._value /= other
        self._propegate()
        return self

    def __ixor__(self, other):
        self._value ^= other
        self._propegate()
        return self


def bind(obj, field_name, form):
    """Given an object and a field name, you can "bind" it to a Formula (or 
    Term). That is, whenever the Formula (or Term) is updated, the field for
    the object is also updated."""
    form._binds.append((obj, field_name))


def fire_on(form):
    """Use as a decorator. If a Formula's truthiness is True, call the
    decorated function."""
    def fire_decorator(func):
        form._fire_on.append(func)
        return func
    return fire_decorator
