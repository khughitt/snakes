################################################################################
#
# {% block header_comment %}
# Abstract clustering template 
# {% endblock %}
#
################################################################################
#
# Cluster dataset and apply one or more functions to each cluster to generate a new feature set
#
#
{% set output_path = "%s/features/%s-%s-{funcs}.csv" | format(output_dir, dat_name, clust_method) -%}

rule cluster_{{ dat_name ~ "_" ~ clust_method | to_rule_name }}:
    input: '{{ cur_input }}'
    output: expand("{{ output_path }}", funcs = {{ clust_params['funcs'] }})
{% block clustering_body %}{% endblock %}

{# add output filenames to list of expected features -#}
{% for func in clust_params['funcs'] %}
    {% set output_file = "%s-%s-%s.csv" | format(dat_name, clust_method, func) %}
    {% do training_set_features.append(output_file) %}
{% endfor %}

