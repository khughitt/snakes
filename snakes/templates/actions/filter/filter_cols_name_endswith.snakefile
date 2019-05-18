        # determine columns to drop
        {% if action.params['drop'] %}
        cols_to_drop = [x for x in dat.columns if x.endswith("{{ action.params['suffix'] }}")]
        {% else %}
        cols_to_drop = [x for x in dat.columns if not x.endswith("{{ action.params['suffix'] }}")]
        {% endif %}
        dat = dat.drop(columns=cols_to_drop)

