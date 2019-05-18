        cols_to_keep = {{ action.params["names"] }}

        # if index column specified, ignore, remove it
        cols_to_keep = [x for x in cols_to_keep if x != dat.index.name]

        dat = dat[cols_to_keep]

