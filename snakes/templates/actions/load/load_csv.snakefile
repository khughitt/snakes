{% extends 'load_tabular_data.snakefile' %}
{% block load_data %}
        dat = pd.read_csv(input[0], sep='{{ dataset.sep }}', index_col={{ dataset.index_col }}, encoding='{{ dataset.encoding }}')
{% endblock %}
