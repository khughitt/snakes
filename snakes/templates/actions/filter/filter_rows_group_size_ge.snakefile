        # apply function to each group and filter results
        dat = filters.filter_rows_by_group_func(dat, "{{ action['group'] }}", "{{ action['group'] }}", 
                                                "len", op=operator.ge, value={{ action['size'] }})


