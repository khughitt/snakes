    run:
        dat = pd.read_csv(input[0], index_col=0)

        fields_to_keep = {{ transform["columns_to_include"] }}
        fields_to_keep = [x for x in fields_to_keep if x != dat.index.name]

        dat[fields_to_keep].to_csv(output[0])


