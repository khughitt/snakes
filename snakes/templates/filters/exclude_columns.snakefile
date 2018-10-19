    run:
        cols_to_drop = {{ filter_params["columns_to_exclude"] }}
        pd.read_csv(input[0], index_col=0).drop(columns=cols_to_drop).to_csv(output[0])
