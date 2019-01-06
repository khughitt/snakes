"""
Snakes cluster aggregation tests
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import AgglomerativeClustering
from snakes import clustering

# set random seed
np.random.seed(0)

# create a random dataset
INPUT = pd.DataFrame(np.random.randint(-100, 100, 50).reshape(5, 10))

# number of test clusters
N_CLUSTERS = 5

# expected clustering (hclust)
hclust = AgglomerativeClustering(n_clusters=N_CLUSTERS, affinity='euclidean', linkage='average')
hclust_clusters = ['cluster_{}'.format(i) for i in hclust.fit_predict(INPUT.T)]

# add cluster column to original data
hclust_df = pd.concat([pd.DataFrame({'cluster': hclust_clusters}), INPUT.T], axis = 1)

# test a few of the aggregation functions; others are tested more exhaustively
# in the gene set test code
@pytest.mark.parametrize("func,expected", [
    ('sum', hclust_df.groupby('cluster').sum().T),
    ('min', hclust_df.groupby('cluster').min().T),
    ('num_positive', hclust_df.groupby('cluster').agg(lambda x: sum(x > 0)).T)
])

def test_hclust_cluster_apply(func, expected):
    """Test gene set aggregation"""
    np.random.seed(0)
    clusters = clustering.cluster(INPUT, 'hclust', N_CLUSTERS)
    pd.testing.assert_frame_equal(expected, clustering.cluster_apply(INPUT, clusters, func))
