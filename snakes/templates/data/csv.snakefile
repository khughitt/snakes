{% extends 'tabular_data.snakefile' %}
{% block load_data %}
        dat = pd.read_table(input[0], sep='{{ dataset.sep }}', index_col={{ dataset.index_col }})
{% endblock %}
