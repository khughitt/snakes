"""
Snakes cluster aggregation functionality
"""
import numpy as np
import pandas as pd
from . import aggregation

def cluster_apply(df, method, n_clusters, func):
    """
    Clusters a dataset and applies a function to the values within each cluster to arrive at a new 
    dataset.

    Arguments
    ---------
    df : pandas.DataFrame
        DataFrame indexed by genes.
    method : str
        Name of clustering method to be applied.        
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

    #
    # cluster dataset
    #
    
    # hierarchical clustering (agglomerative)
    if method == 'hclust':
        from sklearn.cluster import AgglomerativeClustering
        cluster = AgglomerativeClustering(n_clusters=n_clusters, affinity='euclidean',
                                          linkage='average')  
        clusters = cluster.fit_predict(df)  
    else:
        raise Exception("Invalid clustering method specified: {}".format(method))

    # iterate over gene sets and apply function
    for i in range(n_clusters):
        df_subset = df[clusters == i]

        # otherwise, if gene set is non-empty, apply function and store new row and gene set id
        rows.append(tuple(df_subset.apply(func)))

    cluster_labels = ['cluster_{}'.format(i) for i in range(n_clusters)]

    return pd.DataFrame(rows, index=cluster_labels, columns=df.columns)
