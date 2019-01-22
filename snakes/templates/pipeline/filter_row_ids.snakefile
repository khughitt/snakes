    run:
        rows_to_drop = {{ action["rows_to_exclude"] }}
        pd.read_csv(input[0], index_col=0).drop(rows_to_drop).to_csv(output[0])


