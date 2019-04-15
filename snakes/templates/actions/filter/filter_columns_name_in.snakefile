        cols_to_keep = {{ action["names"] }}
        cols_to_keep = [x for x in cols_to_keep if x != dat.index.name]

        dat = dat[cols_to_keep]


