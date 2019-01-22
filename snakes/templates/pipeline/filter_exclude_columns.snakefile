    run:
        cols_to_drop = {{ action["columns_to_exclude"] }}
        pd.read_csv(input[0], index_col=0).drop(columns=cols_to_drop).to_csv(output[0])


