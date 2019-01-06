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
INPUT = pd.DataFrame(np.random.randint(-100, 100, 50).reshape(10, 5))

# number of test clusters
N_CLUSTERS = 3

# expected clustering (hclust)
HCLUST = AgglomerativeClustering(n_clusters=N_CLUSTERS, affinity='euclidean', linkage='average')
HCLUST_CLUSTERS = ['cluster_{}'.format(i) for i in HCLUST.fit_predict(INPUT)]

# add cluster column to original data
HCLUST_DF = pd.concat([pd.DataFrame({'cluster': HCLUST_CLUSTERS}), INPUT.reset_index(drop=True)], 
                      axis = 1)

# test a few of the aggregation functions; others are tested more exhaustively
# in the gene set test code
@pytest.mark.parametrize("func,expected", [
    ('sum', HCLUST_DF.groupby('cluster').sum()),
    ('min', HCLUST_DF.groupby('cluster').min()),
    ('num_positive', HCLUST_DF.groupby('cluster').agg(lambda x: sum(x > 0)))
])

def test_hclust_cluster_apply(func, expected):
    """Test gene set aggregation"""
    np.random.seed(0)
    clusters = clustering.cluster(INPUT, 'hclust', N_CLUSTERS)
    pd.testing.assert_frame_equal(expected, clustering.cluster_apply(INPUT, clusters, func))
