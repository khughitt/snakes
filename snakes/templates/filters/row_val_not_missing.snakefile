    run:
        df = pd.read_csv(input[0])
        df[df['filter_params['field']'].notnull()].to_csv(output[0])
