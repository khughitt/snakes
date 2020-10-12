        func = '{{ action.params["func"] }}'

        # currently, only built-in functions supported by GroupBy may be used
        if func not in dir(pd.core.groupby.GroupBy):
            raise Exception("Invalid aggregation function specified. Must be one supported by pandas.core.groupby.GroupBy")

        # apply aggregation function
        dat = dat.reset_index()
        dat = dat.groupby(dat.columns[0])
        dat = getattr(dat, func)()

