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
        dat = pd.read_csv(input[0], index_col=0)
        dat2 = pd.read_csv(input[1], index_col=0)

        # transpose second dataframe, if requested
        if params.transpose:
            dat2 = dat2.T

        # 
        # determine orientation to compute correlations along.
        #
        # axis = 0; correlate columns of two dataframes (shared row indices)
        # axis = 1; correlate rows of two dataframes (shared column indices)
        #

        # get shared indices
        shared_indices = sorted(list(set(dat.axes[params.axis]).intersection(dat2.axes[params.axis])))

        # determine the length of the longest index to be correlated
        max_dim = max(len(dat.axes[params.axis]), len(dat2.axes[params.axis]))

        if len(shared_indices) == 0:
            raise Exception("No matching indices found!")
        elif len(shared_indices) < max_dim:
            msg = ("Dataset indices are not identical:\n"
                   "Performing correlation using {} / {} shared indices.")
            warnings.warn(msg.format(len(shared_indices), max_dim))

        # limit dataframes to shared indices
        if params.axis == 0:
            # select shared rows
            dat = dat.loc[shared_indices]
            dat2 = dat2.loc[shared_indices]
        else:
            # select shared columns
            dat = dat[shared_indices]
            dat2 = dat2[shared_indices]

        # compute correlations and save result
        dat = dat.apply(lambda x: dat2.corrwith(x, axis=params.axis,
                                                method=params.method), axis=params.axis).to_csv(output[0])


