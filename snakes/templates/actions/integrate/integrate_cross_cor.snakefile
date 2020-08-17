    input: 
        "{{ action.input }}",
        "{{ action.params['dataset'] }}"
    output: '{{ action.output }}'
    params:
        axis={{ action.params['axis'] }},
        transpose={{ action.params['transpose'] }},
        method="{{ action.params['method'] }}"
    run:
        # load datasets
        X = pd.read_feather(input[0])
        X = X.set_index(X.columns[0])

        Y = pd.read_feather(input[1])
        Y = Y.set_index(Y.columns[0])

        # transpose second dataframe, if requested
        if params.transpose:
            Y = Y.T

        # 
        # determine orientation to compute correlations along.
        #
        # axis = 0; correlate columns of two dataframes (shared row indices)
        # axis = 1; correlate rows of two dataframes (shared column indices)
        #

        # get shared indices
        shared_indices = sorted(list(set(X.axes[params.axis]).intersection(Y.axes[params.axis])))

        # determine the length of the longest index to be correlated
        max_dim = max(len(X.axes[params.axis]), len(Y.axes[params.axis]))

        if len(shared_indices) == 0:
            raise Exception("No matching indices found!")
        elif len(shared_indices) < max_dim:
            msg = ("Dataset indices are not identical:\n"
                   "Performing correlation using {} / {} shared indices.")
            warnings.warn(msg.format(len(shared_indices), max_dim))

        # limit dataframes to shared indices
        if params.axis == 0:
            # select shared rows
            X = X.loc[shared_indices]
            Y = Y.loc[shared_indices]
        else:
            # select shared columns
            X = X[shared_indices]
            Y = Y[shared_indices]

        # compute correlations and save result
        X = X.apply(lambda x: Y.corrwith(x, axis=params.axis, method=params.method), axis=params.axis)

        X.reset_index().to_feather(output[0], compression='lz4')


