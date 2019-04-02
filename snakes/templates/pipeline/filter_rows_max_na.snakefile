    run:
        df = pd.read_csv(input[0], index_col=0)
        return filters.filter_rows_by_na(df, op=operator.le, value={{ action['value'] }}, quantile={{ action['quantile'] }}).to_csv(output[0])


