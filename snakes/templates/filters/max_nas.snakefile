    run:
        df = pd.read_csv(input[0], index_col=0)
        df[df.isnull().sum(axis=1) <= {{ filter_params['max_na'] }}].to_csv(output[0])
