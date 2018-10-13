{% extends "clustering.snakefile" %}
{% block header_comment %}Hierarchical clustering workflow ({{ dataset_name }}){% endblock %}
{% block clust_rule %}{{ dataset_name }}_hclust{% endblock %}

