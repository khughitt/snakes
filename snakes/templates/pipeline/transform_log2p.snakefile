    run:
        np.log2(pd.read_csv(input[0], index_col=0) + 1).to_csv(output[0])


