{% extends 'load_tabular_data.snakefile' %}
{% block load_data %}
        dat = pd.read_excel(input[0], sheet='{{ dataset.sheet }}', index_col={{ dataset.index_col }})
{% endblock %}
