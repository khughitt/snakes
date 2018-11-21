    params:
        filter_params = {{ filter_params }} 
    run:
        df = pd.read_csv(input[0], index_col=0)

        # apply stat to each group and filter results
        df = filters.filter_grouped_rows(df, params[0]["group"], params[0]["field"], 
                                         params[0]["stat"], op=operator.le, 
                                         value=params[0]["value"], quantile=params[0]["quantile"])
        df.to_csv(output[0])


