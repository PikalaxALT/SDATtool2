import time


class _ClassPropertyDescriptor(object):
    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self


def classproperty(func):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return _ClassPropertyDescriptor(func)


class Timer:
    def __init__(self, *, print=False):
        self.tic = None
        self.toc = None
        self._print = print

    def __enter__(self):
        self.toc = None
        self.tic = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.toc = time.perf_counter()
        if self._print:
            status = 'Done' if exc_type is None else 'Failed'
            print(f'{status}: ({self.toc - self.tic:.3f})')
