    run:
        df = pd.read_csv(input[0], index_col=0)
        df[df.var(1) > {{ filter_params['cutoff_value'] }}].to_csv(output[0])
