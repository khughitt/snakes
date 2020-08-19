        from sklearn.decomposition import PCA

        # check for missing or non-finite values
        if dat.isna().sum().sum() > 0 or np.isinf(dat).sum().sum() > 0:
            raise Exception("Unable to perform PCA: non-finite values encountered!")

        # if rows are to be projected, transpose the matrix first
        if "{{ action.params['target'] }}" == "rows":
            dat = dat.T

        # store rownames
        row_index = dat.index

        # perform pca projection
        pca = PCA(n_components={{ action.params['num_dims'] }}, whiten={{ action.params['whiten'] }}, random_state={{ action.params['random_seed'] }})
        dat = pca.fit_transform(dat)

        # convert back to a dataframe and restore row and column names
        colnames = ["PC" + str(i + 1) for i in range(dat.shape[1])]
        dat = pd.DataFrame(dat, index = row_index, columns = colnames)

