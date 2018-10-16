{% extends "clustering.snakefile" -%}
{% block header_comment -%}Hierarchical clustering workflow ({{ dataset_name }}){% endblock -%}
{% block clustering_body %}    params: 
        clust_params = {{ clust_params }} 
    script:
        '{{ script_dir }}/aggegation/clustering_hclust.R' 
{% endblock -%}
