"""
Snakes gene set tests
"""
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from snakes import gene_sets

#
# input dataframe
#
#    0   1   2
# a  1   2   3
# b  5  10  15
# c  2   0   0
#
INPUT = pd.DataFrame([[1, 2, 3], [5, 10, 15], [2, 0, 0]], index=['a', 'b', 'c'])

# gene sets
GENE_SETS = {
    'x': ['a', 'c', 'd'],
    'y': ['a', 'b', 'c'],
    'z': ['d', 'e', 'f']
}

@pytest.mark.parametrize("func,expected", [
    ('sum',    [[3, 2, 3], [8, 12, 18]]),
    ('min',    [[1, 0, 0], [1, 0, 0]]),
    ('max',    [[2, 2, 3], [5, 10, 15]]),
    ('mean',   [[1.5, 1.0, 1.5], [8/3, 4.0, 6.0]]),
    ('median', [[1.5, 1.0, 1.5], [2.0, 2.0, 3.0]]),
    ('var',    [list(INPUT.filter(['a', 'c'], axis=0).var()), list(INPUT.var())]),
    ('std',    [list(INPUT.filter(['a', 'c'], axis=0).std()), list(INPUT.std())]),
    ('num_zero', [[0, 1, 1], [0, 1, 1]]),
    ('num_nonzero', [[2, 1, 1], [3, 2, 2]]),
    ('num_positive', [[2, 1, 1], [3, 2, 2]]),
    ('num_negative', [[0, 0, 0], [0, 0, 0]]),
    ('ratio_zero'  ,[[0.0, 0.5, 0.5], [0.0, 1/3, 1/3]]), 
    ('ratio_nonzero', [[1.0, 0.5, 0.5], [1.0, 2/3, 2/3]]),
    ('ratio_positive', [[1.0, 0.5, 0.5], [1.0, 2/3, 2/3]]),
    ('ratio_negative', [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]),
    ('sum_abs', [[3, 2, 3], [8, 12, 18]])
])

def test_gene_set_apply(func, expected):
    """Test gene set aggregation"""
    assert_frame_equal(pd.DataFrame(expected, index=['x', 'y']),
                       gene_sets.gene_set_apply(INPUT, GENE_SETS, func))
