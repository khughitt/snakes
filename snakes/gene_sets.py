"""
Snakes gene set aggregation functionality
"""
import numpy as np
import pandas as pd
from . import aggregation


def gene_set_apply(df, gene_sets, func):
    """
    Aggregates a dataset by specified gene sets and applies a function to the values within each
    gene set to arrive at a new dataset.

    Arguments
    ---------
    df : pandas.DataFrame
        DataFrame indexed by genes.
    gene_sets : dict
        A dictionary mapping from gene set names to lists of gene ids
    func : str
        Name of function or statistic to be applied to each set of gene values. Valid options
        include pandas DataFrame functions, NumPy functions, and a set of custom functions.

    Returns
    -------
    pandas.DataFrame
        A gene set by sample DataFrame containing the aggregated values.
    """
    # parse aggregation function
    func = aggregation.get_agg_func(func)

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
