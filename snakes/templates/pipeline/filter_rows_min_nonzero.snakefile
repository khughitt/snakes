    run:
        df = pd.read_csv(input[0], index_col=0)
        return filters.filter_rows_by_nonzero(df, op=operator.ge, value={{ action['value'] }}, quantile={{ action['quantile'] }}).to_csv(output[0])
