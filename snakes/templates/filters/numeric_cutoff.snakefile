{############################################################################################-#}
{# Template for a simple numeric filter that accepts either an absolute cutoff value (value)
{# or a quantile-based cutoff value (quantile).
{############################################################################################-#}
{% if 'value' in filter_params -%}
    {% set func_args = 'value=%f' | format(filter_params['value']) -%}
{% else -%}
    {% set func_args = 'quantile=%s' | format(filter_params['quantile']) -%}
{% endif %}    run:
        df = pd.read_csv(input[0], index_col=0)
        filters.{% block filter_function %}{% endblock %}(df, {{ func_args }}).to_csv(output[0])
