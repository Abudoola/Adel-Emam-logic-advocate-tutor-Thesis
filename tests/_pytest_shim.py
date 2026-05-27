"""
tests/_pytest_shim.py
---------------------
Minimal stand-in for pytest when it is not installed. Implements:
  - pytest.approx
  - pytest.mark.parametrize (as a no-op decorator that stores the mark)
  - pytest.raises (as a context manager)
"""
class approx:
    def __init__(self, expected, abs=None, rel=None):
        self.expected = expected
        self.abs = abs
        self.rel = rel
    def __eq__(self, other):
        if self.abs is not None:
            return abs(other - self.expected) <= self.abs
        if self.rel is not None:
            return abs(other - self.expected) <= self.rel * abs(self.expected)
        return abs(other - self.expected) <= 1e-7

class _Mark:
    def __init__(self, name, args, kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

class _MarkDecorator:
    def __init__(self, name):
        self.name = name
    def __call__(self, *args, **kwargs):
        def deco(fn):
            mark = _Mark(self.name, args, kwargs)
            existing = getattr(fn, "pytestmark", [])
            fn.pytestmark = existing + [mark]
            return fn
        return deco

class _MarkRoot:
    parametrize = _MarkDecorator("parametrize")
    skip        = _MarkDecorator("skip")
    skipif      = _MarkDecorator("skipif")

mark = _MarkRoot()

class _RaisesCtx:
    def __init__(self, exc): self.exc = exc
    def __enter__(self): return self
    def __exit__(self, et, ev, tb):
        if et is None:
            raise AssertionError(f"Expected {self.exc.__name__}, none raised")
        return issubclass(et, self.exc)

def raises(exc): return _RaisesCtx(exc)
