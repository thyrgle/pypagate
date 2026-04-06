from pypagate.source import SourceMap, exec_always


def test_always():
    source = SourceMap({})
    x = 0
    @exec_always(source)
    def f():
        nonlocal x
        x += 1

    for i in range(3):
        assert x == i
        source.listen({})
