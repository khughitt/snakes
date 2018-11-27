    run:
        df = pd.read_csv(input[0], index_col=0)
        filters.row_value_present(df, "{{ transform['field'] }}").to_csv(output[0])


