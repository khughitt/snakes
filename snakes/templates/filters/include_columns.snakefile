    run:
        cols_to_keep = {{ filter_params["columns_to_include"] }}
        pd.read_csv(input[0], index_col=0)[columns=cols_to_keep].to_csv(output[0])


