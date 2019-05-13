def aggregate_training_sets_input(wildcards):
    checkpoint_output = checkpoints.create_training_sets.get(**wildcards).output[0]
    return expand("{{ output_dir }}/training_sets/{response}.csv", 
                  response=glob_wildcards("{{ output_dir }}/training_sets/{response}.csv").response)

rule aggregate_training_sets:
    input: aggregate_training_sets_input
    output: touch('final.csv')

checkpoint create_training_sets:
  input:
    features={{ wrangler.training_set.input.features }},
    response="{{ wrangler.training_set.input.response }}"
  output: {{ wrangler.training_set.output }}
  params:
    output_dir="{{ output_dir }}/training_sets",
    allow_mismatched_indices={{ config['quality_control']['allow_mismatched_indices'] }}
  run:
    # create output directory
    #os.mkdir(params.output_dir, mode=0o755)

    # load feature data
    feature_dat = pd.read_csv(input.features[0], index_col=0)

    if len(input.features) > 1:
        for filepath in input.features[1:]:
            dat = pd.read_csv(filepath, index_col=0)

            # check to make sure there are no overlapping columns
            if len(set(feature_dat.columns).intersection(dat.columns)) > 0:
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
    response_dat = pd.read_csv(input.response, index_col=0)

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
        # add response data column to end of feature data and save to disk
        feature_dat.join(response_dat[col]).to_csv(os.path.join(params.output_dir, "{}.csv".format(col)))

