    run:
        df = pd.read_csv(input[0], index_col=0)
        filters.row_field_above(df, field='{{ cfg['field'] }}', value={{ cfg['value'] }}, quantile={{ cfg['quantile'] }}).to_csv(output[0])


