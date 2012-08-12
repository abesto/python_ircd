from itertools import chain

def flatten(l):
    return list(chain.from_iterable(l))
