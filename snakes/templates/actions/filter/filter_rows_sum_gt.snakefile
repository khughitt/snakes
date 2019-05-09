        dat = filters.filter_rows_by_func(df=dat, func=np.sum, op=operator.gt, value={{ action.params['value'] }}, quantile={{ action.params['quantile'] }})

