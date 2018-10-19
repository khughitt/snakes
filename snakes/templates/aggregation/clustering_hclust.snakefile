{% extends "clustering.snakefile" -%}
{% block header_comment -%}Hierarchical clustering workflow ({{ dataset_name }}){% endblock -%}
{% block clustering_body %}    params: 
        clust_params = {{ clust_params }},
        dataset_name = '{{ dataset_name }}'
    script:
        '{{ script_dir }}/aggregation/clustering_hclust.R' 
{% endblock -%}
