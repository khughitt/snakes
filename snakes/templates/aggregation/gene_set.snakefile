################################################################################
#
# {% block header_comment %}
# Abstract gene set template 
# {% endblock %}
#
################################################################################
#
# Aggregates gene features into pre-defined gene sets and applies one more functions to derive
# new features.
#
{% set output_path = "%s/features/%s-%s-%s-{funcs}.csv" | format(output_dir, dat_name, gene_set, gmt_name) %}

rule gene_set_{{ dat_name ~ "_" ~ gene_set ~ "_" ~ gmt_name | to_rule_name }}:
    input: '{{ cur_input }}',
           '{{ preprocessed_gmt }}'
    output: expand("{{ output_path }}", funcs = {{ gene_set_params['funcs'] }})
    run:
        # load dataset
        df = pd.read_csv(input[0], index_col=0)
        
        # load gmt file
        entries = [x.rstrip('\n') for x in open(input[1]).readlines()]

        # gmt file column indices
        GENE_SET_NAME  = 0
        GENE_SET_START = 2

        # iterate of gmt entries and construct a dictionary mapping from gene set names to lists
        # the genes they contain
        gene_sets = {}

        for entry in entries:
            # split line and retrieve gene set name and a list of genes in the set
            fields = entry.split('\t')

            gene_sets[fields[GENE_SET_NAME]] = fields[GENE_SET_START:len(fields)]

        # gene set row id prefix
        gset_id_prefix = '{{ dat_name }}_{{ gmt_name | to_rule_name }}'

        # iterate over functions and create one output for each function
        funcs = {{ gene_set_params['funcs'] }}

        for i in range(len(funcs)):
            func = funcs[i]

            # apply function along gene sets and save output
            gset_df = aggregation.gene_set_apply(df, gene_sets, func)

            # update row names to include dataset, gene set, and function applied
            gset_df.index = ["_".join([gset_id_prefix, gene_set, func]) for gene_set in gset_df.index]

            gset_df.to_csv(output[i], index_label='gene_set_id')

{#- add output filenames to list of expected features -#}
{% for func in gene_set_params['funcs'] %}
    {% set output_file = "%s-%s-%s-%s.csv" | format(dat_name, gene_set, gmt_name, func) %}
    {% do training_set_features.append(output_file) %}
{% endfor %}
