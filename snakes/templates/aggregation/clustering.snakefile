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
{% set output_path = "%s/features/%s-%s-{fxns}.csv" | format(output_dir, dataset_name, clust_method) -%}

rule cluster_{{ dataset_name ~ "_" ~ clust_method | to_rule_name }}:
    input: '{{ cur_input }}'
    output: expand("{{ output_path }}", fxns = {{ clust_params['fxns'] }})
{% block clustering_body -%}{% endblock -%}

{# add output filenames to list of expected features -#}
{% for fxn in clust_params['fxns'] -%}
    {% set output_file = "%s-%s-%s.csv" | format(dataset_name, clust_method, fxn) -%}
    {% do training_set_features.append(output_file) -%}
{% endfor -%}

