    run:
        df = pd.read_csv(input[0], index_col=0)
        df = filters.row_max_missing(df, {{ filter_params['value'] }}).to_csv(output[0])