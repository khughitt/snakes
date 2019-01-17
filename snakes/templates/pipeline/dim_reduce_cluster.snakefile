################################################################################
#
# Cluster-based feature aggregation
#
################################################################################
#
# Aggregates gene features using clustering and applies one more functions to derive
# new features.
#
{% set output_path = "%s/data/%s-%s-{funcs}.csv" | format(output_dir, dat_name, clust_method) %}

#{% for dat_name, dat_cfg in data_sources.items() %}
#  {% for clust_params in dat_cfg['clustering'] %}
#    {% set clust_method = clust_params['type'] %}
#    {% set cur_input = "%s/data/%s.csv" | format(output_dir, dat_name) %}

rule cluster_{{ dat_name }}_{{ clust_method | to_rule_name }}:
    input: '{{ cur_input }}'
    output: expand("{{ output_path }}", funcs={{ clust_params['funcs'] }})
    run:
        # load dataset
        df = pd.read_csv(input[0], index_col=0)

        # cluster dataset
        clusters = clustering.cluster(df, '{{ clust_method }}', {{ clust_params['num_clusters'] }})

        # iterate over aggregation functions
        for i, func in enumerate({{ clust_params['funcs'] }}):
            # for each function, cluster the dataset and apply function to each cluster
            res = clustering.cluster_apply(df, clusters, func)
            res.to_csv(output[i], index_label='cluster_id')

{# add output filenames to list of expected datasets #}
{% for func in clust_params['funcs'] %}
    {% set output_file = "%s-%s-%s.csv" | format(dat_name, clust_method, func) %}
    {% do training_set_inputs.append(output_file) %}
{% endfor %}
