"""
Test cases for filtering-related functionality.
"""
import operator
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from snakes import filters

#
# test dataframes
#

# 1. a simple numeric dataframe
#
#    0  1  2
# 0  1  2  3
# 1  1  1  1
# 2  2  3  4
# 3  0  0  0
#
DF_NUMERIC = pd.DataFrame([[1, 2, 3], [1, 1, 1], [2, 3, 4], [0, 0, 0]])

# 2. dataframe with grouped entries
#
#   group  X   Y
# a     A  1   2
# b     A  5  10
# c     A  2   4
# d     B  2   1
# e     B  1   1
# f     B  2   2
# g     C  9   4
# h     D  0   0
#
DF_GROUPED = pd.DataFrame([['A', 1, 2], ['A', 5, 10], ['A', 2, 4],
                           ['B', 2, 1], ['B', 1, 1], ['B', 2, 2],
                           ['C', 9, 4], ['D', 0, 0]],
                          index=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'],
                          columns=['group', 'X', 'Y'])

# 3. dataframe with missing values
#
#      0    1    2 
# 0  1.0  2.0  3.0 
# 1  NaN  NaN  NaN 
# 2  2.0  NaN  4.0 
# 3  0.0  0.0  NaN 
#
DF_MISSING = pd.DataFrame([[1, 2, 3], [None, None, None], [2, None, 4], [0, 0, None]])

#
# column filter tests
#
def test_filter_rows_sum_gt():
    """tests filter_rows_sum_gt function"""
    # 0: all columns
    assert_frame_equal(DF_NUMERIC, filters.filter_rows_by_func(DF_NUMERIC, sum, operator.gt, 0))

    # 4: columns 1,2
    assert_frame_equal(DF_NUMERIC[[1, 2]], filters.filter_rows_by_func(DF_NUMERIC, sum, operator.gt, 4))

    # 8: empty dataframe
    assert_frame_equal(DF_NUMERIC[[]], filters.filter_rows_by_func(DF_NUMERIC, sum, operator.gt, 8))

#
# row filter tests
#
def test_filter_rows_col_gt():
    """tests filter_rows_col_gt function"""
    expected = DF_NUMERIC.iloc[[0, 2]]
    res = filters.filter_rows_by_col(DF_NUMERIC, 1, operator.gt, 1.5)
    assert_frame_equal(expected, res)

def test_filter_rows_col_gt_quantile():
    """tests filter_rows_col_gt function using a quantile-based cutoff"""
    expected = DF_NUMERIC.iloc[[0, 2]]
    res = filters.filter_rows_by_col(DF_NUMERIC, 1, operator.gt, quantile=0.5)
    assert_frame_equal(expected, res)

def test_filter_rows_sum_gt():
    """tests filter_rows_sum_gt function"""
    expected = DF_NUMERIC.iloc[[0, 2]]
    res = filters.filter_rows_by_func(DF_NUMERIC, sum, op=operator.gt, value=0)

    # -1: all rows
    assert_frame_equal(DF_NUMERIC, filters.filter_rows_by_func(DF_NUMERIC, sum, op=operator.gt, value=-1))

    # 0: rows 0-2
    assert_frame_equal(DF_NUMERIC.iloc[[0, 1, 2]], filters.filter_rows_by_func(DF_NUMERIC, sum, op=operator.gt, value=0))

    # 9: empty result
    assert_frame_equal(DF_NUMERIC.iloc[[]], filters.filter_rows_by_func(DF_NUMERIC, sum, op=operator.gt, value=9))

def test_filter_rows_var_gt():
    """tests filter_rows_var_gt function"""
    expected = DF_NUMERIC.iloc[[0, 2]]
    res = filters.filter_rows_by_func(DF_NUMERIC, np.var, op=operator.gt, value=0)
    assert_frame_equal(expected, res)

def test_filter_rows_max_na():
    """tests filter_rows_max_missing function"""
    # 0: first row only
    assert_frame_equal(DF_MISSING.iloc[[0]], filters.filter_rows_by_na(DF_MISSING, op=operator.le, value=0))

    # 1: rows 0,2,3
    assert_frame_equal(DF_MISSING.iloc[[0, 2, 3]], filters.filter_rows_by_na(DF_MISSING, op=operator.le, value=1))

def test_filter_rows_by_group_func():
    """tests test_ function"""
    expected = pd.DataFrame([['A', 1, 2], ['A', 5, 10], ['A', 2, 4],
                             ['C', 9, 4]],
                            index=['a', 'b', 'c', 'g'],
                            columns=['group', 'X', 'Y'])
    res = filters.filter_rows_by_group_func(DF_GROUPED, 'group', 'X', np.sum, op=operator.gt, value=7)
    assert_frame_equal(expected, res)

def test_filter_rows_by_group_size():
    """Tests filtering of groups of rows based on group size."""
    expected = DF_GROUPED.loc[DF_GROUPED['group'].isin(['A', 'B'])]
    res = filters.filter_rows_by_group_func(DF_GROUPED, 'group', 'X', len, op=operator.ge, value=3)
    assert_frame_equal(expected, res)

