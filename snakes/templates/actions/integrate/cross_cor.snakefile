        # load second dataset
        dat2 = pd.read_csv("{{ action.params['dataset'] }}", index_col=0)

        {% if action.params['transpose'] %}
        # transpose dataset
        dat2 = dat2.T
        {% endif %}

        dat = dat2.apply(lambda x: dat.corrwith(x), method="{{ action.params['method'] }}")
