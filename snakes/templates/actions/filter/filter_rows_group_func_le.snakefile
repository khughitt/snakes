        # apply function to each group and filter results
        dat = filters.filter_rows_by_group_func(dat, "{{ action['group'] }}", "{{ action['col'] }}", 
                                               "{{ action['func'] }}", op=operator.le, 
                                               value={{ action['value'] }}, 
                                               quantile={{ action['quantile'] }})


