"""
Snakes gene set aggregation functionality
"""
import numpy as np
import pandas as pd

"""
Custom aggregation functions
"""
_custom_aggregation_funcs = {
    'num_zero'       : lambda x: sum(x == 0),
    'num_nonzero'    : lambda x: sum(x != 0),
    'num_positive'   : lambda x: sum(x > 0),
    'num_negative'   : lambda x: sum(x < 0),
    'ratio_zero'     : lambda x: sum(x == 0) / len(x),
    'ratio_nonzero'  : lambda x: sum(x != 0) / len(x),
    'ratio_positive' : lambda x: sum(x > 0) / len(x),
    'ratio_negative' : lambda x: sum(x < 0) / len(x),
    'sum_abs'        : lambda x: sum(abs(x))
}

def gene_set_apply(df, gene_sets, func):
    """
    Aggregates a dataset by specified gene sets and applies a function to the values within each
    gene set to arrive at a new dataset.

    Note: currently, only numpy functions (e.g. numpy.sum and numpy.median) are supported.

    Arguments
    ---------
    df : pandas.DataFrame
        DataFrame indexed by genes.
    gene_sets : dict
        A dictionary mapping from gene set names to lists of gene ids
    func : function
        Function or statistic to be applied to each set of gene values

    Returns
    -------
    pandas.DataFrame
        A gene set by sample DataFrame containing the aggregated values.
    """
    # find appropriate function to use
    if hasattr(pd.DataFrame, func):
        # pandas (mad)
        pass
    elif hasattr(np, func):
        # numpy (min, max, median, sum, std, var, etc.)
        func = getattr(np, func)
    elif func in _custom_aggregation_funcs.keys():
        # custom aggregation functions (num_positive, abs_sum, etc.)
        func = _custom_aggregation_funcs[func]
    else:
        raise Exception("Invalid gene set aggegration function specified!")

    # list to store aggegration result tuples; will be used to construct a DataFrame
    rows = []

    # list to keep track of gene set for which at least one gene exists in the data
    matched_ids = []

    # iterate over gene sets and apply function
    for gene_set, genes in sorted(gene_sets.items()):
        df_subset = df.filter(genes, axis=0)

        # check to make sure some genes overlap before applying function
        if df_subset.shape[0] == 0:
            continue

        # otherwise, if gene set is non-empty, apply function and store new row and gene set id
        rows.append(tuple(df_subset.apply(func)))
        matched_ids.append(gene_set)

    return pd.DataFrame(rows, index=matched_ids, columns=df.columns)
