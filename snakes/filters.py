"""
Functions for filtering datasets by row, column, or group.
"""
import operator
import numpy as np

#
# Generalized filter functions
#
def filter_data(df, func, axis=1, op=operator.gt, value=None, quantile=None):
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

def filter_rows(df, func, op=operator.gt, value=None, quantile=None):
    """Filters rows from a dataset"""
    return filter_data(df=df, func=func, axis=1, op=op, value=value, quantile=quantile)

def filter_cols(df, func, op=operator.gt, value=None, quantile=None):
    """Filters columns from a dataset"""
    return filter_data(df=df, func=func, axis=0, op=op, value=value, quantile=quantile)

#
# Column-wise filter functions
#
def col_sum_above(df, value=None, quantile=None):
    """Filters dataset to exclude columns whose sum falls below a certain cutoff"""
    return filter_cols(df=df, func=np.sum, op=operator.gt, value=value, quantile=quantile)

def col_var_above(df, value=None, quantile=None):
    """Filters dataset to exclude columns whose variance falls below a certain cutoff"""
    return filter_cols(df=df, func=np.var, op=operator.gt, value=value, quantile=quantile)

def col_max_missing(df, value=None, quantile=None):
    """Filters dataset to exclude columns with too many missing values"""
    # if quantile specified, find associated value
    if quantile is not None:
        value = df.quantile(quantile, axis=1)

    return df[df.isnull().sum(axis=1) <= value]

def col_min_nonzero(df, value=None, quantile=None):
    """Filters dataset to exclude columns with too many zeros"""
    # if quantile specified, find associated value
    if quantile is not None:
        value = df.quantile(quantile, axis=1)

    return df[(df != 0).sum(axis=1) >= value]

def col_value_present(df, field):
    """Returns all columns for which a specific column is not null"""
    return df[df[field].notnull()]

#
# Row-wise filter functions
#
def row_field_above(df, field=None, value=None, quantile=None):
    """Filters dataset to exclude rows for which a specified field falls below a certain cutoff"""
    if quantile is not None:
        value = df[field].quantile(quantile)

    return df[df[field] > value]

def row_sum_above(df, value=None, quantile=None):
    """Filters dataset to exclude rows whose sum falls below a certain cutoff"""
    return filter_rows(df=df, func=np.sum, op=operator.gt, value=value, quantile=quantile)

def row_var_above(df, value=None, quantile=None):
    """Filters dataset to exclude rows whose variance falls below a certain cutoff"""
    return filter_rows(df=df, func=np.var, op=operator.gt, value=value, quantile=quantile)

def row_max_missing(df, value=None, quantile=None):
    """Filters dataset to exclude rows with too many missing values"""
    # if quantile specified, find associated value
    if quantile is not None:
        value = df.quantile(quantile, axis=1)

    return df[df.isnull().sum(axis=1) <= value]

def row_min_nonzero(df, value=None, quantile=None):
    """Filters dataset to exclude rows with too many zeros"""
    # if quantile specified, find associated value
    if quantile is not None:
        value = df.quantile(quantile, axis=1)

    return df[(df != 0).sum(axis=1) >= value]

def row_value_present(df, field):
    """Returns all rows for which a specific column is not null"""
    return df[df[field].notnull()]

def filter_grouped_rows(df, group, field, func, op=operator.gt, value=None, quantile=None):
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
    else:
        # otherwise assume function name or expression passed in as a string
        func = eval(func)

    # apply statistic within each group
    group_stats = df.groupby(group)[field].apply(func)

    # if quantile specified, determine value associated with that quantile
    if quantile is not None:
        cutoff_value = group_stats.quantile(quantile)
    else:
        cutoff_value = value

    # get ids of rows passing the cutoff
    mask = group_stats.loc[op(group_stats, cutoff_value)].index

    return df[df[group].isin(mask)]

def filter_row_min_group_size(df, group, size):
    """
    Filters groups of rows that are not of a specified size or larger
    """
    return df.groupby(group).filter(lambda x: len(x) >= size)

