{############################################################################################-#}
{# Template for a simple numeric filter that accepts either an absolute cutoff value (value) 
{# or a quantile-based cutoff value (quantile).
{#############################################################################################}    run:
        df = pd.read_csv(input[0], index_col=0)
        filters.{% block filter_function %}{% endblock %}(df, value={{ filter_params['value'] }}, quantile={{ filter_params['quantile'] }}).to_csv(output[0])
