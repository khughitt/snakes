from collections.abc import Mapping


def recursive_update(d, u):
    """
    recursive dictionary update

    d: dict
        Dictionary to be updated
    u: dict
        Dictionary being applied

    source: https://stackoverflow.com/a/3233356/554531
    """
    for k, v in u.items():
        if isinstance(v, Mapping):
            d[k] = recursive_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d
