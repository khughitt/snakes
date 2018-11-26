{% extends "clustering.snakefile" %}
{% block header_comment %}Hierarchical clustering workflow ({{ dat_name }})
{% endblock %}
{% block clustering_body %}    params: 
        clust_params = {{ clust_params }},
        dat_name = '{{ dat_name }}'
    script:
        '{{ script_dir }}/clustering/hclust.R' 
{% endblock %}
