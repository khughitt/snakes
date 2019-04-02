"""
Functions for filtering datasets by row, column, or group.
"""
import operator
import numpy as np

#
# Generalized filter function
#
def filter_data_by_func(df, func, axis=1, op=operator.gt, value=None, quantile=None):
    """Generalized function for filtering a dataset by rows or columns."""
    # aply function along specified axis
    vals = df.apply(func, axis=axis)

    # if quantile specified, find associated value
    if quantile is not None:
        value = vals.quantile(quantile, axis=axis)

    # apply operator
    mask = op(vals, value)

    # apply function along rows or columns and return filtered result
    if axis == 1:
        # rows
        return df[mask]
    else:
        # columns
        return df[mask.index[mask]]

#
# Row-wise filter functions
#
def filter_rows_by_func(df, func, op=operator.gt, value=None, quantile=None):
    """Filters rows from a dataset"""
    return filter_data_by_func(df=df, func=func, axis=1, op=op, value=value, quantile=quantile)

def filter_rows_by_col(df, col=None, op=operator.gt, value=None, quantile=None):
    """Filter rows in a dataset based on their value for a specific column"""
    if quantile is not None:
        value = df[col].quantile(quantile)

    return df[op(df[col], value)]

def filter_rows_by_na(df, op=operator.le, value=None, quantile=None):
    """Filters dataset rows based on the number of missing values"""
    if quantile is not None:
        value = df.quantile(quantile, axis=1)

    return df[op(df.isnull().sum(axis=1), value)]

def filter_rows_by_nonzero(df, op=operator.gt, value=None, quantile=None):
    """Filters dataset rows based on the number of 0's present"""
    if quantile is not None:
        value = df.quantile(quantile, axis=1)

    return df[op((df != 0).sum(axis=1), value)]

def filter_rows_col_not_na(df, col):
    """Returns all rows for which a specific column is not null"""
    return df[df[col].notnull()]

def filter_rows_col_val_in(df, col, values):
    """
    Removes all rows for which a column is not one of a specified set of values
    """
    return df[df[col].isin(values)]


def filter_rows_col_val_not_in(df, col, values):
    """
    Removes all rows for which a column is one of a specified set of values
    """
    return df[~df[col].isin(values)]

def filter_rows_by_group_func(df, group, col, func, op=operator.gt, value=None, quantile=None):
    """
    Filters groups of rows based on some function applied for a column within each group.

    For example, this could be used to filter out all entries for drugs which have a low
    variance of IC-50 scores across cell lines.
    """
    # determine which function to apply within each group
    if func == 'mad':
        # median absolute deviation (mad)
        from statsmodels import robust
        func = robust.mad
    elif isinstance(func, str):
        # otherwise assume function name or expression passed in as a string
        func = eval(func)

    # apply statistic within each group
    group_stats = df.groupby(group)[col].apply(func)

    # if quantile specified, determine value associated with that quantile
    if quantile is not None:
        cutoff_value = group_stats.quantile(quantile)
    else:
        cutoff_value = value

    # get ids of rows passing the cutoff
    mask = group_stats.loc[op(group_stats, cutoff_value)].index

    return df[df[group].isin(mask)]

#
# Column-wise filter functions
#
def filter_cols_by_func(df, func, op=operator.gt, value=None, quantile=None):
    """Filters columns from a dataset"""
    return filter_data_by_func(df=df, func=func, axis=0, op=op, value=value, quantile=quantile)

