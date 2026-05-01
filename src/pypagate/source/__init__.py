from collections.abc import Callable
from numbers import Number
from pypagate import Formula, Term


class SourceMap:
    """A collection of Terms (with starting values) where Terms can 
        be updated with the `listen` method."""
    def __init__(self, terms: dict[str, Number]):
        for name, value in terms:
            self.__dict__[name] = Term(value)

        self._exec_while: list[tuple[Formula, Callable]] = []
        self._exec_always: list[Callable] = []

    def __getitem__(self, item):
        return self.__dict__[item]

    def listen(self, terms: dict[str, Number]):
        """Take in a new set of values and update them all.

        :param terms: Dictionary of terms to take in and "listen" too. These
            will then update the values in `self`.
        """
        # Update the values.
        for name, value in terms:
            self[name].change(value)
        # Issue an evaluation of every formula from these terms.
        for form, func in self._exec_while:
            if form.unwrap():
                func()
        # Avoid a branch condition, execute these funcs always on every call
        # to listen.
        for func in self._exec_always:
            func()

def exec_while(form, source):
    """Use as a decorator: Every time source.listen(...) is called *and* the 
    formula evaluates to `True`, execute this function.

    :param form: The formula to check if it evaluates to `True`.
    :param source: The source that triggers `listen(...)`.
    """
    def decorator(func):
        source._exec_while.append((form, func))
        return func
    return decorator

def exec_always(source):
    """Use as a decorator: Every time source.listen(...) is called, evaluate 
    this function.
    
    :param source: The source that triggers `listen(...)`.
    """
    def decorator(func):
        source._exec_always.append(func)
        return func
    return decorator

def exec_either(form, f, g, source):
    """Either executes ``f`` if ``form`` evaluates to ``True`` or ``g`` if 
    ``form`` evaluates to ``False`` whenever ``source.listen(...)`` is called.

    :param form: The ``Formula`` to test against.
    :param f: The function to execute if ``form`` is ``True``.
    :param g: The function to execute if ``form`` is ``False``.
    :param source: Either ``f`` or ``g`` is executed whenever
       source.listen(...) is called."""
    @exec_always(source)
    def func():
        if form.unwrap():
            return f()
        return g()
    return func
