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
{% set output_path = "%s/features/%s-%s-{fxns}.csv" | format(config['output_dir'], dataset_name, clust_method) -%}

rule cluster_{% block clust_rule %}{% endblock %}:
    input: '{{ cur_input }}'
    output: expand("{{ output_path }}", fxns = {{ clust_params['fxns'] }})
    run:
        pass

