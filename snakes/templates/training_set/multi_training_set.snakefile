checkpoint create_training_sets:
  input:
    features={{ wrangler.training_set.input.features }},
    response="{{ wrangler.training_set.input.response }}"
  output: directory("{{ wrangler.training_set.output }}")
  params:
    output_dir="{{ wrangler.training_set.output }}",
    allow_mismatched_indices={{ wrangler.training_set.options['allow_mismatched_indices'] }},
    include_column_prefix={{ wrangler.training_set.options['include_column_prefix'] }}
  run:
    # create output directory
    if not os.path.exists(params.output_dir):
        os.mkdir(params.output_dir, mode=0o755)

    # load feature data
    feature_dat = pd.read_feather(input.features[0])
    feature_dat = feature_dat.set_index(feature_dat.columns[0]).sort_index()

    # update column names (optional)
    if params.include_column_prefix:
        prefix = pathlib.Path(input.features[0]).stem + "_"
        feature_dat.columns = prefix + feature_dat.columns

    if len(input.features) > 1:
        for filepath in input.features[1:]:
            dat = pd.read_feather(filepath)
            dat = dat.set_index(dat.columns[0]).sort_index()


            # update column names (optional)
            if params.include_column_prefix:
                prefix = pathlib.Path(filepath).stem + "_"
                dat.columns = prefix + dat.columns

            # check to make sure there are no overlapping columns
            shared_columns = set(feature_dat.columns).intersection(dat.columns)

            if len(shared_columns) > 0:
                msg = f"Column names in {filepath} overlap with others in feature data."
                raise ValueError(msg)

            # check for index mismatches
            if not params.allow_mismatched_indices and not dat.index.equals(feature_dat.index):
                msg = f"Row names for {filepath} do not match other feature data indices."
                raise ValueError(msg)

            # merge feature data
            feature_dat = feature_dat.join(dat)

            # check to make sure dataset is not empty
            if feature_dat.empty:
                from pandas.errors import EmptyDataError
                msg = (f"Training set empty after merging {filepath}! Check to make "
                       "sure datasets have row names in common")
                raise EmptyDataError(msg)

    # load response dataframe
    response_dat = pd.read_feather(input.response)
    response_dat = response_dat.set_index(response_dat.columns[0]).sort_index()

    # check for index mismatches
    if not params.allow_mismatched_indices and not response_dat.index.equals(feature_dat.index):
        msg = f"Row names for {input.response} do not match feature data indices."
        raise ValueError(msg)

    # check to make sure at least some shared indices exist
    if len(set(feature_dat.index).intersection(response_dat.index)) == 0:
        from pandas.errors import EmptyDataError
        msg = (f"Feature and response data have no shared row names!")
        raise EmptyDataError(msg)

    # iterate over columns in response data and create training sets
    for col in response_dat.columns:
        # get response column as a Series and rename to "response"
        dat = response_dat[col]
        dat.name = 'response'

        # add response data column to end of feature data and save to disk
        outfile = os.path.join(params.output_dir, "{}.feather".format(col))
        feature_dat.join(dat).reset_index().to_feather(outfile, compression='lz4')

