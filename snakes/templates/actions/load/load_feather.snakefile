{% extends 'load_tabular_data.snakefile' %}
{% block load_data %}
        dat = pd.read_feather(input[0])
        dat = dat.set_index(dat.columns[{{ dataset.index_col }}])
{% endblock %}
