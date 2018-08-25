import sys


def import_int():
    try:
        from builtins import int
    except ImportError:
        pass


def crange():
    pass
