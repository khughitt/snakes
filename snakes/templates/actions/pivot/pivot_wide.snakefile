        {% set index='"' ~ action.params['index'] ~ '"' if action.params['index'] != None else None %}
        dat = dat.pivot(index={{ index }}, columns="{{ action.params['columns'] }}", values="{{ action.params['values'] }}")

