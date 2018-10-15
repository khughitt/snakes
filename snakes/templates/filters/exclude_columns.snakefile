    run:
        pd.read_csv(input[0], index_col=0).drop(columns={{ filter_params["columns_to_exclude"] }}).to_csv(output[0])
