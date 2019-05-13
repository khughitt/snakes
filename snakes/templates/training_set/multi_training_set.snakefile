def aggregate_training_sets_input(wildcards):
    checkpoint_output = checkpoints.create_training_sets.get(**wildcards).output[0]
    return expand("{{ output_dir }}/training_sets/{response}.csv", 
                  response=glob_wildcards("{{ output_dir }}/training_sets/{response}.csv").response)

rule aggregate_training_sets:
    input: aggregate_training_sets_input
    output: touch('final.csv')

checkpoint create_training_sets:
  input:
    features={{ config['training_sets']['features'] }},
    response="{{ config['training_sets']['response'] }}"
  output: {{ config['training_sets']['output'] }}
  run:
    # create output directory
    output_dir = "{{ config['training_sets']['output_dir'] }}"
    os.mkdir(output_dir, mode=0o755)

    # load feature data
    feature_dat = pd.read_csv(input.features[0], index_col=0)

    if len(input.features) > 1:
        for filepath in input.features[1:]:
            dat = pd.read_csv(filepath, index_col=0)
            feature_dat = feature_dat.join(dat)

    # load response dataframe
    response_dat = pd.read_csv(input.response, index_col=0)

    # iterate over columns in response data and create training sets
    for col in response_dat.columns:
        feature_dat.join(response_dat[col]).to_csv(os.path.join(output_dir, "{}.csv".format(col)))

