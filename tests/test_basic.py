from pypagate import Term, fire_on, permit, on_change


def test_inc():
    x = Term(5)
    y = x + 1
    assert y.unwrap() == 6
    x += 1
    assert y.unwrap() == 7

def test_two_terms():
    x = Term(6)
    y = Term(7)
    z = x + y
    assert z.unwrap() == 13
    x += 1
    assert z.unwrap() == 14
    assert x.unwrap() == 7
    assert y.unwrap() == 7

def test_func_listen():
    y = 0
    assert y == 0
    x = Term(1)
    @fire_on(x == 3)
    def f():
        nonlocal y
        y = 3
    assert y == 0
    x += 1
    assert x.unwrap() == 2
    assert y == 0
    x += 1
    assert y == 3

def test_permit():
    y = True
    x = Term(3)
    @permit(x == 0)
    def f():
        nonlocal y
        y = False
    x -= 1
    f()
    assert y
    x -= 1
    f()
    assert y
    x -= 1
    f()
    assert not y

def test_on_change():
    y = 0
    x = Term(0)
    @on_change(x)
    def f(old, new):
        nonlocal y
        y += 1
    assert y == 0
    x += 1
    assert y == 1
    x += 1
    assert y == 2

