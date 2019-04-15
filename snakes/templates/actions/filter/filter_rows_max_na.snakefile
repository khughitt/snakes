        dat = filters.filter_rows_by_na(dat, op=operator.le, value={{ action['value'] }}, quantile={{ action['quantile'] }})


