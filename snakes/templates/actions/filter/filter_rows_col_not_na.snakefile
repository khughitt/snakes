    run:
        df = pd.read_csv(input[0], index_col=0)
        filters.filter_rows_col_not_na(df, "{{ action['col'] }}").to_csv(output[0])


