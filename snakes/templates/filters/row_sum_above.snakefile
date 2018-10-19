    run:
        df = pd.read_csv(input[0], index_col=0)
        df[df.sum(1) > {{ filter_params['value'] }}].to_csv(output[0])
