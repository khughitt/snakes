    run:
        dat = pd.read_csv(input[0], index_col=0)
        dat = dat.apply(lambda x: (x - np.mean(x)) / np.std(x), axis={{ action['axis'] }})
        dat.to_csv(output[0])


