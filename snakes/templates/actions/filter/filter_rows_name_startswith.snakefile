        # determine rows to drop
        {% if action.params['drop'] %}
        rows_to_drop = [x for x in dat.index if x.startswith("{{ action.params['prefix'] }}")]
        {% else %}
        rows_to_drop = [x for x in dat.index if not x.startswith("{{ action.params['prefix'] }}")]
        {% endif %}
        dat = dat.drop(index=rows_to_drop, axis=1)

