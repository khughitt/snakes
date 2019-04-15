        dat = filters.filter_rows_by_col(dat, col='{{ action['col'] }}', op=operator.gt, value={{ action['value'] }}, quantile={{ action['quantile'] }})


