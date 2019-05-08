"""
Snakes aggregation functionality
"""
import pandas as pd
import sys

_aggregation = sys.modules[__name__]


def get_agg_func(func):
    """
    Takes an aggregation function string reference and returns either a string or function that 
    pandas can interpret.

    Arguments
    ---------
    func: str
        String representation of a function to be applied to dataset groups (e.g. "sum")
    """
    if hasattr(pd.DataFrame, func):
        # pandas (e.g. min, max, sum, mad, etc.)
        return func
    elif hasattr(_aggregation, func):
        # custom aggregation functions (e.g. num_positive, abs_sum, etc.)
        return getattr(_aggregation, func)

    # if function does not match any of the above, raise an exception
    raise Exception("Invalid gene set aggegration function specified!")


"""
Custom aggregation functions
"""


def num_zero(x):
    return sum(x == 0)


def num_nonzero(x):
    return sum(x != 0)


def num_positive(x):
    return sum(x > 0)


def num_negative(x):
    return sum(x < 0)


def ratio_zero(x):
    return sum(x == 0) / len(x)


def ratio_nonzero(x):
    return sum(x != 0) / len(x)


def ratio_positive(x):
    return sum(x > 0) / len(x)


def ratio_negative(x):
    return sum(x < 0) / len(x)


def sum_abs(x):
    return sum(abs(x))
