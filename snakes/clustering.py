"""
Snakes cluster aggregation functionality
"""
import numpy as np
import pandas as pd
from . import aggregation

def cluster(df, method, n_clusters):
    """
    Clusters a dataset using a specified clustering method and number of clusters.

    Note: currently only hierarchical clustering (hclust) is supported.

    Arguments
    ---------
    df : pandas.DataFrame
        DataFrame indexed by genes.
    method : str
        Name of clustering method to be applied
    n_clusters: int
        Number of clusters to partition data into

    Returns
    -------
    out: list
        A list of cluster identifiers in the same order as the dataset rows
    """
    # hierarchical clustering (agglomerative)
    if method == 'hclust':
        from sklearn.cluster import AgglomerativeClustering
        res = AgglomerativeClustering(n_clusters=n_clusters, affinity='euclidean',
                                          linkage='average')
        return res.fit_predict(df)

    # if not valid cluster method was specified, raise an error
    raise Exception("Invalid clustering method specified: {}".format(method))

def cluster_apply(df, clusters, func):
    """
    Given a dataset partitioning, applies a specified function to each partition of a dataset

    Arguments
    ---------
    df : pandas.DataFrame
        DataFrame indexed by genes.
    clusters: list
        List of cluster identifiers associated with each row in df
    func : str
        Name of function or statistic to be applied to each set of gene values. Valid options
        include pandas DataFrame functions, NumPy functions, and a set of custom functions.

    Returns
    -------
    pandas.DataFrame
        A gene set by sample DataFrame containing the aggregated values.
    """
    # find appropriate function to use
    if hasattr(pd.DataFrame, func):
        # pandas (e.g. mad)
        pass
    elif hasattr(np, func):
        # numpy (e.g. min, max, median, sum, std, var, etc.)
        func = getattr(np, func)
    elif hasattr(aggregation, func):
        # custom aggregation functions (e.g. num_positive, abs_sum, etc.)
        func = getattr(aggregation, func)
    else:
        raise Exception("Invalid gene set aggegration function specified!")

    # list to store aggegration result tuples; will be used to construct a DataFrame
    rows = []

    # iterate over gene sets and apply function
    for i in range(len(clusters)):
        df_subset = df[clusters == i]

        # otherwise, if gene set is non-empty, apply function and store new row and gene set id
        rows.append(tuple(df_subset.apply(func)))

    cluster_labels = ['cluster_{}'.format(i) for i in range(len(clusters))]

    return pd.DataFrame(rows, index=cluster_labels, columns=df.columns)
