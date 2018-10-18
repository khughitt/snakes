    run:
        df = pd.read_csv(input[0])
        df = df.groupby('filter_params["group"]')['filter_params["field"]']

        # function / statistic to apply to each group
        stat = filter_params['stat']
        
        # check to make sure supported function / statistic specified
        if stat == 'len':
            # length
            fxn = len
        elif stat == 'mad':
            # median absolute deviation (mad)
            from statsmodels import robust
            fxn = robust.mad
        else:
            raise("Invalid min_group_stat statistic specified!")

        # if quantile specified, determine value associated with that quantile
        if 'quantile' in filter_params:
            df.apply(fxn)
            cutoff_value = df.apply(fxn).quantile(filter_params['quantile'])
        else:
            cutoff_value = filter_params['value']

        # apply stat to each group and filter results
        df.filter(lambda x: fxn(x) >= cutoff_value).to_csv(output[0])

