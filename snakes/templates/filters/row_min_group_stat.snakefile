    run:
        df = pd.read_csv(input[0])

        # determine when absolute or relative cutoff specified
        quantile = filter_params['quantile'] if 'quantile' in filter_params else None
        value = filter_params['value'] if 'value' in filter_params else None
        
        # apply stat to each group and filter results
        df = filters.filter_grouped_rows(df, 'filter_params["group"]', 'filter_params["field"]', 
                                        filter_params['stat'], op=operator.ge, value=value,
                                        quantile=quantile)
        df.to_csv(output[0])

