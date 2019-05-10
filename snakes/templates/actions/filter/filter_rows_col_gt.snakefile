        dat = filters.filter_rows_by_col(dat, col='{{ action.params['col'] }}',
        op=operator.gt, value={{ action.params['value'] }}, quantile={{ action.params['quantile'] }})

