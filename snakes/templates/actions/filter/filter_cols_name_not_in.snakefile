        cols_to_drop = {{ action.params["names"] }}
        dat = dat.drop(columns=cols_to_drop)

