run:
        dat = pd.read_csv(input, index_col=0)
        dat = (dat / dat.sum()) * 1E6
        dat.to_csv(output)
