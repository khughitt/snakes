    run:
        df = pd.read_csv(input[0], index_col=0)
        filters.row_field_above(df, field='{{ transform['field'] }}', value={{ transform['value'] }}, quantile={{ transform['quantile'] }}).to_csv(output[0])


