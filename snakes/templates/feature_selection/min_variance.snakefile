  run:
    params = params[0]

    # check to make sure at least one of the two required parameters is set
    if params['value'] is None and params['quantile'] is None:
        msg = f"Either 'value' or 'quantile' must be specified for rule '{'{{ rule.rule_id }}'}'"
        raise ValueError(msg)

    # load training set data
    dat = pd.read_feather(input[0])

    # get names of feature columns
    feat_cols = dat.columns[:-1]

    # compute variance of each column
    col_vars = dat.drop(dat.columns[0], axis=1).var()

    # determine cutoff to use
    if params['value'] is not None:
        cutoff = params['value']
    elif params['quantile'] is not None:
        cutoff = col_vars.quantile(params['quantile'])

    # apply filter and save result
    cols_to_keep = [dat.columns[0]] + dat[feat_cols].loc[:, col_vars >= cutoff].columns

    dat[cols_to_keep].to_feather(output[0], compression='lz4')
