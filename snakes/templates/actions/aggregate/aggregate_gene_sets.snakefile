    run:
        df = pd.read_csv(input[0], index_col=0)
        
        # load gmt file
        entries = [x.rstrip('\n') for x in open('{{ action["gmt"] }}').readlines()]

        # gmt file column indices
        GENE_SET_NAME  = 0
        GENE_SET_START = 2

        # iterate of gmt entries and construct a dictionary mapping from gene set names to lists
        # the genes they contain
        gsets = {}

        for entry in entries:
            # split line and retrieve gene set name and a list of genes in the set
            fields = entry.split('\t')

            gsets[fields[GENE_SET_NAME]] = fields[GENE_SET_START:len(fields)]

        # apply function along gene sets and save output
        gset_df = gene_sets.gene_set_apply(df, gsets, '{{ action["func"] }}')

        # update row names to include dataset, gene set, and function applied
        #gset_df.index = ["_".join([gset_id_prefix, gene_set, func]) for gene_set in gset_df.index]
        gset_df.to_csv(output[0], index_label='gene_set_id')


