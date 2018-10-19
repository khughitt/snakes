    run:
        df = pd.read_csv(input[0], index_col=0)
        filters.row_var_above(df, {{ filter_params['value'] }}).to_csv(output[0])
