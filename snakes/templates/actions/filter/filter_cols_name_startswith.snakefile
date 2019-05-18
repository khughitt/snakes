        {% if action.params['drop'] %}
        cols_to_drop = [x for x in dat.columns if x.startswith("{{ action.params['prefix'] }}")]
        {% else %}
        cols_to_drop = [x for x in dat.columns if not x.startswith("{{ action.params['prefix'] }}")]
        {% endif %}
        dat = dat.drop(columns=cols_to_drop)

