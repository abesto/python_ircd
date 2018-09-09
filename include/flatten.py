"""
`flatten`: Flatten arbitrarily deeply nested lists
"""
from typing import List, Any


def flatten(data: List) -> List[Any]:
    """
    Flatten an arbitrarily deeply nested list of lists.
    Argument not fully typed pending recursive types, see https://github.com/python/mypy/issues/731
    """
    if not isinstance(data, list):
        return data
    ret = []
    for item in data:
        if isinstance(item, list):
            ret.extend(flatten(item))
        else:
            ret.append(item)
    return ret
