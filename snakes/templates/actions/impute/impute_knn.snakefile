        from sklearn.impute import KNNImputer

        imputer = KNNImputer(n_neighbors={{ action.params['k'] }})

        dat[:] = imputer.fit_transform(dat)


