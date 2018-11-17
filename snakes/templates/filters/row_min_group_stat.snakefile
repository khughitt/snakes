    params:
        filter_params = {{ filter_params }} 
    run:
        df = pd.read_csv(input[0])

        # determine when absolute or relative cutoff specified
        #quantile = params[0]['quantile'] if 'quantile' in params[0] else None
        #value = params[0]['value'] if 'value' in params[0] else None
        
        # apply stat to each group and filter results
        df = filters.filter_grouped_rows(df, params[0]["group"], params[0]["field"], 
                                         params[0]["stat"], op=operator.ge, 
                                         value=params[0]["value"], quantile=params[0]["quantile"])
        df.to_csv(output[0])

