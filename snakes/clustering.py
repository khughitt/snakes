"""
Snakes cluster aggregation functionality
"""
import numpy as np
import pandas as pd
from . import aggregation

def hclust(df, n_clusters):
    """
    Performs hierarchical clustering on a dataset

    Arguments
    ---------
    df : pandas.DataFrame
        DataFrame indexed by genes.
    n_clusters: int
        Number of clusters to partition data into

    Returns
    -------
    out: list
        A list of cluster identifiers in the same order as the dataset rows
    """
    # hierarchical clustering (agglomerative)
    from sklearn.cluster import AgglomerativeClustering
    hclust = AgglomerativeClustering(n_clusters=n_clusters, affinity='euclidean',
                                        linkage='average')
    clusters = hclust.fit_predict(df)

    # convert numeric cluster ids to strings and return
    return ['cluster_{}'.format(i) for i in clusters]

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
    # parse aggregation function
    func = aggregation.get_agg_func(func)

    # transpose dat and add cluster column
    df = pd.concat([pd.DataFrame({'cluster': clusters}), df.reset_index(drop=True)], axis = 1)

    # apply function to elements in each cluster and revert to original orientation
    return df.groupby('cluster').agg(func)
