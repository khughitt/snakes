    run:
        df = pd.read_csv(input[0], index_col=0)
        filters.row_field_above(df, field='{{ filter_params['field'] }}', value={{ filter_params['value'] }}, quantile={{ filter_params['quantile'] }}).to_csv(output[0])


