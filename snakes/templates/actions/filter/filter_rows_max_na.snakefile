        dat = filters.filter_rows_by_na(dat, op=operator.le, 
                                        value={{ action.params['value'] }}, quantile={{ action.params['quantile'] }})


