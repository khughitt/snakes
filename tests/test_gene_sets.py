"""
Snakes gene set tests
"""
import pandas as pd
from pandas.testing import assert_frame_equal
from snakes import gene_sets

# test data
df = pd.DataFrame([[1, 2, 3], [5, 10, 15], [0, 0, 0]], index=['a', 'b', 'c'])

gsets = {
    'x': ['a', 'c', 'd'],
    'y': ['a', 'b', 'c'],
    'z': ['d', 'e', 'f']
}

def test_gene_set_apply():
    expected = pd.DataFrame([[1, 2, 3], [6, 12, 18]], index=['x', 'y'])

    assert_frame_equal(expected, gene_sets.gene_set_apply(df, gsets, 'sum'))

