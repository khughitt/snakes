    run:
        df = pd.read_csv(input[0], index_col=0)

        # apply stat to each group and filter results
        df = filters.filter_grouped_rows(df, "{{ cfg['group'] }}", "{{ cfg['field'] }}", 
                                         "{{ cfg['stat'] }}", op=operator.ge, 
                                         value="{{ cfg['value'] }}", 
                                         quantile="{{ cfg['quantile'] }}")
        df.to_csv(output[0])


