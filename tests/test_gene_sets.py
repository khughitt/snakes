"""
Snakes gene set tests
"""
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from snakes import gene_sets

# input dataframe
df = pd.DataFrame([[1, 2, 3], [5, 10, 15], [2, 0, 0]], index=['a', 'b', 'c'])

# gene sets
gsets = {
    'x': ['a', 'c', 'd'],
    'y': ['a', 'b', 'c'],
    'z': ['d', 'e', 'f']
}

@pytest.mark.parametrize("func,expected", [
    ('sum', pd.DataFrame([[3, 2, 3], [8, 12, 18]], index=['x', 'y'])),
    ('min', pd.DataFrame([[1, 0, 0], [1, 0, 0]], index=['x', 'y'])),
    ('max', pd.DataFrame([[2, 2, 3], [5, 10, 15]], index=['x', 'y'])),
    ('mean', pd.DataFrame([[1.5, 1.0, 1.5], [8/3, 4.0, 6.0]], index=['x', 'y']))
])
def test_gene_set_apply(func, expected):
    # expected = pd.DataFrame([[1, 2, 3], [6, 12, 18]], index=['x', 'y'])
    # assert_frame_equal(expected, gene_sets.gene_set_apply(df, gsets, 'sum'))
    assert_frame_equal(expected, gene_sets.gene_set_apply(df, gsets, func))

