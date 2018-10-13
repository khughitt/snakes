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
{% set output_str = config['output_dir'] + '/' + dataset_name + '/clusters-' + clust_method + 
                    '/' + dataset_name + '-' + clust_method + '-{fxns}.csv' -%}

rule cluster_{% block clust_rule %}{% endblock %}:
    input: '{{ cur_input }}'
    output: expand("{{ output_str }}", fxns = {{ clust_params['fxns'] }})
    run:
        # todo

