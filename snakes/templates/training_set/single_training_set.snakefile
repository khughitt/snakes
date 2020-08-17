rule create_training_sets:
  input:
    features={{ config['training_sets']['features'] }},
    response="{{ config['training_sets']['response'] }}"
  output: {{ config['training_sets']['output'] }}
  run:
    # create output directory
    #output_dir = os.path.basename(output[0])
    #os.mkdir(output_dir, mode=0o755)

    # load feature data
    feature_dat = pd.read_feather(input.features[0])
    feature_dat = feature_dat.set_index(feature_dat.columns[0])

    if len(input.features) > 1:
        for filepath in input.features[1:]:
            dat = pd.read_feather(filepath)
            dat = dat.set_index(dat.columns[0])
            feature_dat = feature_dat.join(dat)

    # load response dat
    response_dat = pd.read_feather(input.response)
    response_dat = response_dat.set_index(response_dat.columns[0])

    # combine into a single training set and save
    feature_dat.join(response_dat).reset_index().to_feather(output[0], compression='lz4')
