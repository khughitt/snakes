    run:
        df = pd.read_csv(input[0], index_col=0)
        filters.filter_rows_by_col(df, col='{{ action['col'] }}', op=operator.gt, value={{ action['value'] }}, quantile={{ action['quantile'] }}).to_csv(output[0])


