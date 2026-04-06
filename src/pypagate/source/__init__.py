from collections.abc import Callable
from numbers import Number
from pypagate import Formula, Term


class SourceMap:
    def __init__(self, terms: dict[str, Number]):
        """Create a collection of Terms and values."""
        for name, value in terms:
            self.__dict__[name] = Term(value)

        self._exec_while: (Formula, Callable) = []
        self._exec_always: Callable = []

    def listen(self, terms: dict[str, Number]):
        """Take in a new set of values and update them all."""
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
    """Every time source.listen(...) is called and the formula is true, execute
    this function."""
    def decorator(func):
        source._exec_while.append((form, func))
        return func
    return decorator

def exec_always(source):
    """Every time source.listen(...) is called, evaluate this function."""
    def decorator(func):
        source._exec_always.append(func)
        return func
    return decorator
