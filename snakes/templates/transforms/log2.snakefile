run:
        np.log2(pd.read_csv(input, index_col=0)).to_csv(output)
