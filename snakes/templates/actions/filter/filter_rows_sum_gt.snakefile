        dat = filters.filter_rows_by_func(df=dat, func=np.sum, op=operator.gt, value={{ action['value'] }}, quantile={{ action['quantile'] }})

