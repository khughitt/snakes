"""
Snakes custom aggregation functions
"""
num_zero = lambda x: sum(x == 0)
num_nonzero = lambda x: sum(x != 0)
num_positive = lambda x: sum(x > 0)
num_negative = lambda x: sum(x < 0)
ratio_zero = lambda x: sum(x == 0) / len(x)
ratio_nonzero = lambda x: sum(x != 0) / len(x)
ratio_positive = lambda x: sum(x > 0) / len(x)
ratio_negative = lambda x: sum(x < 0) / len(x)
sum_abs = lambda x: sum(abs(x))

