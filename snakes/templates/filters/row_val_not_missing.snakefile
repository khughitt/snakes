    run:
        df = pd.read_csv(input[0])
        filters.row_value_present(df, {{ filter_params['field'] }}).to_csv(output[0])
