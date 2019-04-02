    run:
        df = pd.read_csv(input[0], index_col=0)
        return filters.filter_rows(df=df, func=np.var, op=operator.gt, value={{ action['value'] }}, quantile={{ action['quantile'] }}).to_csv(output[0])


