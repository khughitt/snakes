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
{% set output_path = "%s/features/%s-%s-%s-{fxns}.csv" | format(output_dir, dataset_name, gene_set, gmt_name) -%}

rule gene_set_{{ dataset_name ~ "_" ~ gene_set ~ "_" ~ gmt_name | to_rule_name }}:
    input: '{{ cur_input }}',
           '{{ preprocessed_gmt }}'
    output: expand("{{ output_path }}", fxns = {{ gene_set_params['fxns'] }})
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

        # iterate over functions and create one output for each function
        fxns = {{ gene_set_params['fxns'] }}

        for i in range(len(fxns)):
            fxn = fxns[i]

            # validate function (currently, only numpy methods supported)
            if not hasattr(np, fxn):
                raise("Invalid gene set aggegration function specified!")

            # list to store aggegration result tuples; will be used to construct a DataFrame
            rows = []

            # list to keep track of gene set for which at least one gene exists in the data
            gene_sets_matched = []

            # iterate over gene sets and apply function
            for gene_set, genes in gene_sets.items():
                df = df.filter(genes, axis=0)

                # check to make sure some genes overlap before applying function
                if df.shape[0] > 0:
                    gene_sets_matched.append(gene_set)
                    rows.append(tuple(df.apply(getattr(np, fxn))))

            # extend row id to include datatype, gmt, and aggregation fxn
            gene_set_ids = ["_".join(['{{dataset_name}}', '{{gmt_name | to_rule_name}}', gene_set, fxn]) for gene_set in gene_sets_matched]

            pd.DataFrame(rows, index=gene_set_ids, columns=df.columns).to_csv(output[i], index_label='gene_set_id')

{# add output filenames to list of expected features -#}
{% for fxn in gene_set_params['fxns'] -%}
    {% set output_file = "%s-%s-%s-%s.csv" | format(dataset_name, gene_set, gmt_name, fxn) -%}
    {% do training_set_features.append(output_file) %}
{% endfor %}
