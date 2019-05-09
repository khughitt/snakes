        # apply function to each group and filter results
        dat = filters.filter_rows_by_group_func(dat, "{{ action.params['group'] }}", 
                                                "{{ action.params['col'] }}", 
                                                "{{ action.params['func'] }}", 
                                                op=operator.le, 
                                                value={{ action.params['value'] }}, 
                                                quantile={{ action.params['quantile'] }})


