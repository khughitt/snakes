    run:
        df = pd.read_csv(input[0], index_col=0)

        # apply function to each group and filter results
        df = filters.filter_rows_by_group_func(df, "{{ action['group'] }}", "{{ action['col'] }}", 
                                               "{{ action['func'] }}", op=operator.le, 
                                               value={{ action['value'] }}, 
                                               quantile={{ action['quantile'] }})
        df.to_csv(output[0])
