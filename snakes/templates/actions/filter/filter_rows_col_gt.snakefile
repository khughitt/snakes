        dat = filters.filter_rows_by_col(dat, col='{{ action.params['col'] }}', op=operator.gt, value={{ action['value'] }}, quantile={{ action['quantile'] }})

