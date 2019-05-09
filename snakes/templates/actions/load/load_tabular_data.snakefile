    run:
{% block load_data %}{% endblock %}
{% if config.development.enabled and config.development.sample_row_frac < 1 %}
        # sub-sample dataset rows
        dat = dat.sample(frac={{ config.development.sample_row_frac }}, random_state={{ config.random_seed }}, axis=0)
{% endif %}
{% if config.development.enabled and config.development.sample_col_frac < 1 %}
        # sub-sample dataset columns
        dat = dat.sample(frac={{ config.development.sample_col_frac }}, random_state={{ config.random_seed }}, axis=1)
{% endif %}
        dat.to_csv(output[0], index_label='{{ dataset.xid }}')


