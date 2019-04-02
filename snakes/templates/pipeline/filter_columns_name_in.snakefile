    run:
        dat = pd.read_csv(input[0], index_col=0)

        cols_to_keep = {{ action["names"] }}
        cols_to_keep = [x for x in cols_to_keep if x != dat.index.name]

        dat[cols_to_keep].to_csv(output[0])


