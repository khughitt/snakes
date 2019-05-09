        # apply function to each group and filter results
        dat = filters.filter_rows_by_group_func(dat, "{{ action.params['group'] }}", 
                                                "{{ action.params['group'] }}", 
                                                "len", op=operator.ge, 
                                                value={{ action.params['size'] }})


