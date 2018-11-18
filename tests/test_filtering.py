"""
Test cases for filtering-related functionality.
"""
import operator
import pandas as pd
from pandas.testing import assert_frame_equal
from snakes import filters

# test dataset
df = pd.DataFrame([['A', 1, 2], ['A', 5, 10], ['A', 2, 4],
                  ['B', 2, 1], ['B', 1, 1], ['B', 2, 2],
                  ['C', 9, 4], ['D', 0, 0]], 
                  index=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'],
                  columns=['group', 'X', 'Y'])

def test_filter_grouped_rows():
    expected = pd.DataFrame([['A', 1, 2], ['A', 5, 10], ['A', 2, 4],
                            ['C', 9, 4]], 
                    index=['a', 'b', 'c', 'g'],
                    columns=['group', 'X', 'Y'])
    res = filters.filter_grouped_rows(df, 'group', 'X', 'sum', op=operator.gt, value=7)
    assert_frame_equal(expected, res)
