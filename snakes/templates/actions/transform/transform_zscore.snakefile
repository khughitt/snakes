        dat = dat.apply(lambda x: (x - np.mean(x)) / np.std(x), axis={{ action['axis'] }})

