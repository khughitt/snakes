    run:
        df = pd.read_csv(input[0], index_col=0)
        filters.filter_rows_col_gt(df, col='{{ action['col'] }}', value={{ action['value'] }}, quantile={{ action['quantile'] }}).to_csv(output[0])


