from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from itertools import product
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
    if isinstance(form, Term) or (not form._needs_update):
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
def _register_bin_op(bin_op: Callable[[Any, Any], Any]):
    """Helper function intended to help construct binary operations (like 
    __add__) for Formula and Term."""
    def b(self: Formula | Term, other: Formula | Term | Number):
        if isinstance(other, Number):
            other = Term(other)
        formula = Formula(bin_op=bin_op, _lhs=self, _rhs=other)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula
    return b

def _register_rbin_op(bin_op: Callable[[Any, Any], Any]):
    """Helper function intended to help construct binary operations (like 
    __radd__) for Formula and Term."""
    def b(self: Formula | Term, other: Formula | Term | Number):
        if isinstance(other, Number):
            other = Term(other)
        # Order of params are switched for the r version!
        formula = Formula(bin_op=bin_op, _lhs=other, _rhs=self)
        self._parents.append(formula)
        other._parents.append(formula)
        return formula
    return b

def _register_unary_op(unary_op: Callable[[Any], Any]):
    """Helper function inteded to help construct unary operations (like
    __abs__) for Formula and Term."""
    def u(self: Formula | Term):
        formula = Formula(unary_op=unary_op, _rhs=self)
        self._parents.append(formula)
        return formula
    return u 

@dataclass
class Formula:
    """A Well-Formed-Formula that consists of Term objects (i.e. variables) and 
    operators."""
    _value: Any = None
    unary_op: Callable[[Any], Any] | None = None
    _lhs: Formula | None = None
    bin_op: Callable[[Any, Any], Any] | None = None 
    _rhs: Formula | None = None
    _parents: list[Formula] = field(default_factory=list)
    _binds: Any = field(default_factory=list)
    _fire_on: list[Callable] = field(default_factory=list)
    _on_change: list[Callable] = field(default_factory=list)
    _needs_update: bool = True

    def _update(self):
        new_value = evaluate(self)
        # For the on_change decorator.
        if new_value != self._value:
            for func in self._on_change:
                func(self._value, new_value)
        self._value = new_value
        for parent in self._parents:
            parent._needs_update = True
            parent._update()
        for obj, field_name in self._binds:
            setattr(obj, field_name, self._value)
        for func in self._fire_on:
            if self.unwrap(): # If the value has True truthiness, call the 
                 func()       # function.
        self._needs_update = False

    def unwrap(self):
        """Get the value the formula currently evaluates to."""
        if self._needs_update:
            return evaluate(self)
        return self._value

    def __str__(self):
        # Bypass Python's name mangling by directly accessing the runtime globals
        if not self.bin_op:
            unary_map = globals().get("__unary_str_map", {})
            op_name = unary_map.get(self.unary_op, getattr(self.unary_op, "__name__", "op"))
            return op_name + " (" + str(self._rhs) + ")"
            
        bin_map = globals().get("__bin_str_map", {})
        return f"({str(self._lhs)}) {bin_map.get(self.bin_op, 'op')} ({str(self._rhs)})"    
    
    # Binary operations
    __add__ = _register_bin_op(operator.add)
    __radd__ = _register_rbin_op(operator.add)
    __sub__ = _register_bin_op(operator.sub)
    __rsub__ = _register_rbin_op(operator.sub)
    __pow__ = _register_bin_op(operator.pow)
    __rpow__ = _register_rbin_op(operator.pow)
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

    # Comparison operators. 
    # NOTE: We ignore bad-override error from Pyrefly. This is because normally
    # these operators return booleans, but we do *not* want to do that.
    __lt__ = _register_bin_op(operator.lt) # pyrefly: ignore[bad-override]
    __rlt__ = _register_rbin_op(operator.lt) # pyrefly: ignore[bad-override]
    __gt__ = _register_bin_op(operator.gt) # pyrefly: ignore[bad-override]
    __rgt__ = _register_rbin_op(operator.gt) # pyrefly: ignore[bad-override]
    __ge__ = _register_bin_op(operator.ge) # pyrefly: ignore[bad-override]
    __rge__ = _register_rbin_op(operator.ge) # pyrefly: ignore[bad-override]
    __eq__ = _register_bin_op(operator.eq) # pyrefly: ignore[bad-override]
    __req__ = _register_rbin_op(operator.eq) # pyrefly: ignore[bad-override]
    __ne__ = _register_bin_op(operator.ne) # pyrefly: ignore[bad-override]
    __rne__ = _register_rbin_op(operator.ne) # pyrefly: ignore[bad-override]

def _register_ibin_op(bin_op: Callable[[Any, Any], Any]):
    """Helper function intended to help construct binary operations (like 
    __radd__) for Formula and Term."""
    def b(self: Formula | Term, other: Number):
        new_value = bin_op(self._value, other)
        if new_value != self._value:
            # Something did change.
            # Execute _on_change funcs.
            for func in self._on_change:
                func(self._value, new_value)
            # Since it changed, also check truthiness and execute
            # corresponding functions.
            if self.unwrap():
                for func in self._fire_on:
                    func()
        self._value = new_value
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
    _fire_on: list[Callable] = field(default_factory=list)
    _on_change: list[Callable] = field(default_factory=list)
    _var_count: int = 0 # Terms do not contribute variable count, but variables
                        # do!

    def _propegate(self):
        for parent in self._parents:
            parent._needs_update = True
            parent._update()
        # Even a lonesome Term may be bound to a field.
        for obj, field_name in self._binds:
            setattr(obj, field_name, self._value)
        # or it may also be given a contract.
        if self.unwrap():
            for func in self._fire_on:
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
        # Execute _on_change funcs.
        for func in self._on_change:
            func()
        # Execute _on_fire funcs if the Term has truthiness of True
        if self.unwrap():
            for func in self._fire_on:
                func()
        # Continue updating.
        self._value = new_value
        self._propegate()

    def unwrap(self):
        """Returns the value of the Term at the current moment."""
        return self._value

    def __str__(self):
        return f"Term({self._value})"

    # Binary operators
    __add__ = _register_bin_op(operator.add)
    __radd__ = _register_rbin_op(operator.add)
    __sub__ = _register_bin_op(operator.sub)
    __rsub__ = _register_rbin_op(operator.sub)
    __pow__ = _register_bin_op(operator.pow)
    __rpow__ = _register_rbin_op(operator.pow)
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
    # NOTE: We override bad-override because these operators *traditionally*
    # return a boolean but we want them to *not* do that.
    __lt__ = _register_bin_op(operator.lt) # pyrefly: ignore[bad-override]
    __rlt__ = _register_rbin_op(operator.lt) # pyrefly: ignore[bad-override]
    __gt__ = _register_bin_op(operator.gt) # pyrefly: ignore[bad-override]
    __rgt__ = _register_rbin_op(operator.gt) # pyrefly: ignore[bad-override]
    __ge__ = _register_bin_op(operator.ge) # pyrefly: ignore[bad-override]
    __rge__ = _register_rbin_op(operator.ge) # pyrefly: ignore[bad-override]
    __eq__ = _register_bin_op(operator.eq) # pyrefly: ignore[bad-override]
    __req__ = _register_rbin_op(operator.eq) # pyrefly: ignore[bad-override]
    __ne__ = _register_bin_op(operator.ne) # pyrefly: ignore[bad-override]
    __rne__ = _register_rbin_op(operator.ne) #pyrefly: ignore[bad-override]

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


def bind(obj: Any, field_name: Any, form: Formula | Term):
    """Given an object and a field name, you can "bind" it to a Formula (or 
    Term). That is, whenever the Formula (or Term) is updated, the field for
    the object is also updated.

    :param obj: The object to update.
    :param field_name: The field specific field of `obj` to change.
    :param form: A Formula or Term that `obj.field` is updated to be equivalent
        to.
    """
    form._binds.append((obj, field_name))

def fire_on(form: Formula | Term, *args, **kwargs):
    """Use as a decorator: If a Formula's truthiness is True, call the
    decorated function.

    :param form: Execute the proceeding function if `form` evaluates to True at
        some point in time.
    :param args: Additional positional arguments to pass to the decorated function.
    :param kwargs: Additional keyword arguments to pass to the decorated function.
    """
    def fire_decorator(func):
        def wrapped():
            return func(*args, **kwargs)
        form._fire_on.append(wrapped)
        return func
    return fire_decorator

def permit(form: Formula | Term, *args, **kwargs):
    """Use as a decorator: If a Formula's truthiness is True, allow the
    decorated function to be called, otherwise calling the decorated function
    does nothing.

    :param form: *Allow* execution of the proceeding function if `form`
        evaluates to true at the time of calling the proceeding function.
    :param args: Additional positional arguments to pass to the decorated function.
    :param kwargs: Additional keyword arguments to pass to the decorated function.
    """
    def permit_decorator(func):
        def f(*f_args, **f_kwargs):
            if form.unwrap():
                return func(*args, *f_args, **{**kwargs, **f_kwargs})
            else:
                return (lambda: None)()
        return f
    return permit_decorator

def either(form: Formula | Term, f: Callable[[]], g: Callable[[]]):
    """Creates a new function with name ``name`` that, when called, executes
    ``f`` when ``form`` is ``True`` and ``g`` when ``form`` is ``False``.

    :param form: ``Formula`` to test.
    :param f: Function to evaluate when ``form`` is ``True``.
    :param g: Function to evaluate when ``form`` is ``False``
    """
    def func():
        if form.unwrap():
            return f()
        return g()
    return func

def on_change(form: Formula | Term, *args, **kwargs):
    """Use as a decorator: If a Formula's truthiness is True, call the
    decorated function.

    :param form: Execute the proceeding function if `form` evaluates to True at
        some point in time.
    :param args: Additional positional arguments to pass to the decorated function.
    :param kwargs: Additional keyword arguments to pass to the decorated function.
    """
    def fire_decorator(func):
        def wrapped(old, new):
            return func(old, new, *args, **kwargs)
        form._on_change.append(wrapped)
        return func
    return fire_decorator


def verify_any(law: Law):
    for instance in law._specializations:
        if instance.unwrap():
            return True
    return False

def verify_all(law: Law):
    for instance in law._specializations:
        if not instance.unwrap():
            return False
        return True


def _specialize_helper(law: Law | Variable, parent=None):
    if isinstance(law, Variable):
        if parent is not None:
            law._temp_value._parents.append(parent)
        return law._temp_value
    elif isinstance(law, Term):
        return law
    else:
        if law.bin_op is None:
            form = Formula(unary_op=law.unary_op,
                           _rhs=None)
            rhs = _specialize_helper(law._rhs, parent=form)
            form._rhs = rhs
            if parent is not None:
                form._parents.extend(parent)
            return form     
        else:
            form = Formula(
                    bin_op=law.bin_op,
                    _lhs=None,
                    _rhs=None
                   )
            lhs = _specialize_helper(law._lhs, parent=form)
            rhs = _specialize_helper(law._rhs, parent=form)
            form._lhs = lhs
            form._rhs = rhs
            if parent is not None:
                form._parents.extend(parent)
            return form


def _specialize(law: Law | Variable, subs: list[Term]):
    """Generates a Formula for the specified Terms."""
    if isinstance(law, Variable):
        return subs[0]
    for i, var in enumerate(law.variables):
        var._temp_value = subs[i]
    return _specialize_helper(law)

@dataclass
class Universe:
    entities: Term[Any] = field(default_factory=list)

# Similar to here https://stackoverflow.com/a/7844038/667648
def _law_register_bin_op(bin_op: Callable[[Any, Any], Any]):
    """Helper function intended to help construct binary operations (like 
    __add__) for Formula and Term."""
    def b(self: Law | Variable, other: Law | Variable | Number):
        if isinstance(other, Number):
            other = Term(other)
            vc = self._var_count
            law = Law(self.universe,
                      self.variables,
                      bin_op=bin_op, _lhs=self, _rhs=other, _var_count=vc)
        elif isinstance(other, Variable):
            other = Term(other)
            vc = self._var_count
            law = Law(self.universe,
                      self.variables + [other],
                      bin_op=bin_op, _lhs=self, _rhs=other, _var_count=vc)
        else:
            other = Term(other)
            vc = self._var_count + other._var_count
            law = Law(self.universe,
                      self.variables + other.variables,
                      bin_op=bin_op, _lhs=self, _rhs=other, _var_count=vc)
        self._parents.append(law)
        other._parents.append(law) # pyrefly: ignore[missing-attribute]
                                   # other is gaurenteed to have _parents. If 
                                   # it were a Number, it gets reassigned to a 
                                   # Term.
        return law
    return b

def _law_register_rbin_op(bin_op: Callable[[Any, Any], Any]):
    """Helper function intended to help construct binary operations (like 
    __radd__) for Formula and Term."""
    def b(self: Law, other):
        if isinstance(self, Variable):
            self.variables = []
        if isinstance(other, Number) or isinstance(other, Term):
            other = Term(other)
            vc = self._var_count
            # Order of params are switched for the r version!
            law = Law(self.universe,
                      self.variables,
                      bin_op=bin_op, _lhs=other, _rhs=self, _var_count=vc)
        elif isinstance(other, Variable):
            vc = self._var_count + 1
            # Order of params are switched for the r version!
            law = Law(self.universe,
                      self.variables + [other],
                      bin_op=bin_op, _lhs=other, _rhs=self, _var_count=vc)
        else:
            vc = self._var_count + other._var_count
            law = Law(self.universe,
                      self.variables + other.variables,
                      bin_op=bin_op, _lhs=self, _rhs=other, _var_count=vc)
        self._parents.append(law)
        other._parents.append(law)
        return law
    return b

def _law_register_unary_op(unary_op):
    """Helper function inteded to help construct unary operations (like
    __abs__) for Formula and Term."""
    def u(self):
        if isinstance(self, Variable):
            self.variables = []
        if isinstance(self, Variable):
            return Law(self.universe,
                       [self],
                       unary_op=unary_op, _rhs=self, _var_count=1)
        vc = self._var_count
        law = Law(self.universe,
                  self.variables,
                  unary_op=unary_op, _rhs=self, _var_count=vc)
        self._parents.append(law)
        return law
    return u 


@dataclass
class Variable:
    universe: Universe
    _var_count: int = 1
    _temp_value: Any = None
    _parents: list[Law] = field(default_factory=list)

    def __post_init__(self):
        self.variables: list[Variable] = [self]

    # Binary operations
    __add__ = _law_register_bin_op(operator.add)
    __radd__ = _law_register_rbin_op(operator.add)
    __sub__ = _law_register_bin_op(operator.sub)
    __rsub__ = _law_register_rbin_op(operator.sub)
    __pow__ = _law_register_bin_op(operator.pow)
    __rpow__ = _law_register_rbin_op(operator.pow)
    __mul__ = _law_register_bin_op(operator.mul)
    __rmul__ = _law_register_rbin_op(operator.mul)
    __truediv__ = _law_register_bin_op(operator.truediv)
    __rtruediv__ = _law_register_rbin_op(operator.truediv)
    __floordiv__ = _law_register_bin_op(operator.floordiv)
    __rfloordiv__ = _law_register_rbin_op(operator.floordiv)
    __xor__ = _law_register_bin_op(operator.xor)
    __rxor__ = _law_register_rbin_op(operator.xor)

    # Unary operations
    __abs__ = _law_register_unary_op(operator.abs)
    __not__ = _law_register_unary_op(operator.not_)
    __pos__ = _law_register_unary_op(operator.pos)
    __neg__ = _law_register_unary_op(operator.neg)

    # Comparison operators.
    # NOTE: We ignore bad-override because these operators *traditionally*
    # return a boolean but we do not want that in our case.
    __lt__ = _law_register_bin_op(operator.lt) # pyrefly: ignore[bad-override]
    __rlt__ = _law_register_rbin_op(operator.lt) # pyrefly: ignore[bad-override]
    __gt__ = _law_register_bin_op(operator.gt) # pyrefly: ignore[bad-override]
    __rgt__ = _law_register_rbin_op(operator.gt) # pyrefly: ignore[bad-override]
    __ge__ = _law_register_bin_op(operator.ge) # pyrefly: ignore[bad-override]
    __rge__ = _law_register_rbin_op(operator.ge) # pyrefly: ignore[bad-override]
    __eq__ = _law_register_bin_op(operator.eq) # pyrefly: ignore[bad-override]
    __req__ = _law_register_rbin_op(operator.eq) # pyrefly: ignore[bad-override]
    __ne__ = _law_register_bin_op(operator.ne) # pyrefly: ignore[bad-override]
    __rne__ = _law_register_rbin_op(operator.ne) # pyrefly: ignore[bad-override]



@dataclass
class Law:
    universe: Universe
    variables: list[Variable] = field(default_factory=list)
    unary_op: Callable[[Any], Any] | None = None
    _lhs: Law | None = None
    bin_op: Callable[[Any, Any], Any] | None = None 
    _rhs: Law | None = None
    _parents: list[Law] = field(default_factory=list)
    _binds: Any = field(default_factory=list)
    _fire_on: list[Callable] = field(default_factory=list)
    _on_change: list[Callable] = field(default_factory=list)
    _needs_update: bool = True
    _var_count: int = 0
    _specializations: list[Formula] = field(default_factory=list)
    
    def __post_init__(self):
        substitutions = product(self.universe.entities, repeat=self._var_count)
        # The law is the union of the specialization.
        for substitution in substitutions:
            self._specializations.append(_specialize(self, substitution))

    # Binary operations
    __add__ = _law_register_bin_op(operator.add)
    __radd__ = _law_register_rbin_op(operator.add)
    __sub__ = _law_register_bin_op(operator.sub)
    __rsub__ = _law_register_rbin_op(operator.sub)
    __pow__ = _law_register_bin_op(operator.pow)
    __rpow__ = _law_register_rbin_op(operator.pow)
    __mul__ = _law_register_bin_op(operator.mul)
    __rmul__ = _law_register_rbin_op(operator.mul)
    __truediv__ = _law_register_bin_op(operator.truediv)
    __rtruediv__ = _law_register_rbin_op(operator.truediv)
    __floordiv__ = _law_register_bin_op(operator.floordiv)
    __rfloordiv__ = _law_register_rbin_op(operator.floordiv)
    __xor__ = _law_register_bin_op(operator.xor)
    __rxor__ = _law_register_rbin_op(operator.xor)

    # Unary operations
    __abs__ = _law_register_unary_op(operator.abs)
    __not__ = _law_register_unary_op(operator.not_)
    __pos__ = _law_register_unary_op(operator.pos)
    __neg__ = _law_register_unary_op(operator.neg)

    # Comparison operators. 
    __lt__ = _law_register_bin_op(operator.lt) # pyrefly: ignore[bad-override]
    __rlt__ = _law_register_rbin_op(operator.lt) # pyrefly: ignore[bad-override]
    __gt__ = _law_register_bin_op(operator.gt) # pyrefly: ignore[bad-override]
    __rgt__ = _law_register_rbin_op(operator.gt) # pyrefly: ignore[bad-override]
    __ge__ = _law_register_bin_op(operator.ge) # pyrefly: ignore[bad-override]
    __rge__ = _law_register_rbin_op(operator.ge) # pyrefly: ignore[bad-override]
    __eq__ = _law_register_bin_op(operator.eq) # pyrefly: ignore[bad-override]
    __req__ = _law_register_rbin_op(operator.eq) # pyrefly: ignore[bad-override]
    __ne__ = _law_register_bin_op(operator.ne) # pyrefly: ignore[bad-override]
    __rne__ = _law_register_rbin_op(operator.ne) # pyrefly: ignore[bad-override]


def fire_on_each(law: Law, *args, **kwarg):
    """Use as a decorator: If some specialization of a Law's truthiness is 
    True, call the decorated function.

    :param form: Execute the proceeding function if `form` evaluates to True 
        at some point in time.
    :param args: Additional positional arguments to pass to the decorated 
        function.
    :param kwargs: Additional keyword arguments to pass to the decorated 
        function.
    """
    def fire_decorator(func):
        def wrapped():
            return func(*args, **kwarg)
        for form in law._specializations:
            form._fire_on.append(wrapped)
        return func
    return fire_decorator
