"""
Test cases for filtering-related functionality.
"""
import operator
import pandas as pd
from pandas.testing import assert_frame_equal
from snakes import filters

#
# test dataframes
#

# 1. a simple numeric dataframe
DF_NUMERIC = pd.DataFrame([[1, 2, 3], [1, 1, 1], [2, 3, 4], [0, 0, 0]])

# 2. dataframe with grouped entries
DF_GROUPED = pd.DataFrame([['A', 1, 2], ['A', 5, 10], ['A', 2, 4],
                           ['B', 2, 1], ['B', 1, 1], ['B', 2, 2],
                           ['C', 9, 4], ['D', 0, 0]], 
                          index=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'],
                          columns=['group', 'X', 'Y'])

#
# test functions
#
def test_filter_row_var_above():
    """tests filter_row_var_above function"""
    expected = DF_NUMERIC.iloc[[0, 2]]
    res = filters.row_var_above(DF_NUMERIC, value=0)
    assert_frame_equal(expected, res)

def test_filter_grouped_rows():
    """tests test_filter_grouped_rows function"""
    expected = pd.DataFrame([['A', 1, 2], ['A', 5, 10], ['A', 2, 4],
                             ['C', 9, 4]],
                            index=['a', 'b', 'c', 'g'],
                            columns=['group', 'X', 'Y'])
    res = filters.filter_grouped_rows(DF_GROUPED, 'group', 'X', 'sum', op=operator.gt, value=7)
    assert_frame_equal(expected, res)
