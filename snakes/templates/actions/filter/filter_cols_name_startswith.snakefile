        cols_to_drop = [x for x in dat.columns if x.endswith("{{ action.params['prefix'] }}")]
        dat = dat.drop(columns=cols_to_drop)

