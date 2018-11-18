"""
Functions for filtering datasets by row, column, or group.
"""
import operator
import numpy as np

def filter_data(df, func, axis=1, op=operator.gt, value=None, quantile=None):
    """Generalized function for filtering a dataset by rows or columns."""
    # if quantile specified, find associated value
    if quantile is not None:
        value = df.quantile(quantile, axis=axis)

    # apply function along rows or columns and return filtered result
    return df[op(df.apply(func, axis=axis), value)]

def filter_rows(df, func, op=operator.gt, value=None, quantile=None):
    """Filters rows from a dataset"""
    return filter_data(df=df, func=func, axis=1, op=op, value=value, quantile=quantile)

def filter_cols(df, func, op=operator.gt, value=None, quantile=None):
    """Filters columns from a dataset"""
    return filter_data(df=df, func=func, axis=2, op=op, value=value, quantile=quantile)

def row_sum_above(df, value=None, quantile=None):
    """Filters dataset to exclude rows below a certain cutoff"""
    return filter_rows(df=df, func=np.sum, op=operator.gt, value=value, quantile=quantile)

def row_var_above(df, value=None, quantile=None):
    """Filters dataset to exclude rows below a certain cutoff"""
    # return df[df.var(axis=1) > value]
    return filter_rows(df=df, func=np.var, op=operator.gt, value=value, quantile=quantile)

def row_max_missing(df, value=None, quantile=None):
    """Filters dataset to exclude rows with too many missing values"""
    # if quantile specified, find associated value
    if quantile is not None:
        value = df.quantile(quantile, axis=axis)

    return df[df.isnull().sum(axis=1) <= value]

def row_min_nonzero(df, value=None, quantile=None):
    """Filters dataset to exclude rows with too many zeros"""
    # if quantile specified, find associated value
    if quantile is not None:
        value = df.quantile(quantile, axis=axis)

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
    print('[DEV] running filter_grouped_rows')
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
    mask = group_stats.loc[group_stats > cutoff_value].index

    return(df[df[group].isin(mask)])
