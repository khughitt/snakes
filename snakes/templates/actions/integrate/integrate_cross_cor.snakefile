    input: 
        "{{ action.input }}",
        "{{ action.params['dataset'] }}"
    output: '{{ action.output }}'
    run:
        # load datasets
        dat = pd.read_csv(input[0], index_col=0)
        dat2 = pd.read_csv(input[1], index_col=0)

        {% if action.params['transpose'] %}
        # transpose dataset
        dat2 = dat2.T
        {% endif %}

        # get shared columns
        shared_cols = sorted(list(set(dat.columns).intersection(dat2.columns)))

        max_cols = max(len(dat.columns), len(dat2.columns))

        if len(shared_cols) == 0:
            raise Exception("No matching columns found!")
        elif len(shared_cols) < max_cols:
            msg = ("Dataset columns are not identical:\n"
                   "Performing correlation using {} / {} shared columns.")
            warnings.warn(msg.format(len(shared_cols), max_cols))

        # normalize columns
        dat = dat[shared_cols]
        dat2 = dat2[shared_cols]

        dat = dat2.apply(lambda x: dat.corrwith(x, method="{{ action.params['method'] }}")).to_csv(output[0])


