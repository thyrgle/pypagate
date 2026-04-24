from collections.abc import Callable
from numbers import Number
from pypagate import Formula, Term


class SourceMap:
    """A collection of Terms (with starting values) where Terms can 
        be updated with the `listen` method."""
    def __init__(self, terms: dict[str, Number]):
        for name, value in terms:
            self.__dict__[name] = Term(value)

        self._exec_while: list[(Formula, Callable)] = []
        self._exec_always: list[Callable] = []
        self._exec_either: list[(Formula, Callable, Callable)] = []

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
        # Perform either evaluations.
        for form, f, g in self._exec_either:
            if form.unwrap():
                f()
            else:
                g()
        # Avoid a branch condition, execute these funcs always on every call
        # to listen.
        for func in self._exec_always:
            func()


def exec_either(f, g, form, source):
    """Use on a decorator for an *empty* function: Will perform either f or g
    when ``source.listen(...)`` is executed. Whether ``f`` or ``g`` is executed
    depends on whether ``form`` is ``True`` (``f``) or ``False`` (``g``).

    :param f: Function that will execute when ``form`` is ``True``.
    :param g: Function that will execute when ``form`` is ``False``.
    :param form: The formula that decides which function will execute.
    :param source: Source to listen to.
    """
    def decorator(func):
        source._exec_either.append((form, f, g))
        return func
    return decorator

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
