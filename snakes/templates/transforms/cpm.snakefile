    run:
        df = pd.read_csv(input[0], index_col=0)
        df = (df / df.sum()) * 1E6
        df.to_csv(output[0])


