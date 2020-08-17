        # map gene identifiers
        #import mygene
        #mg = mygene.MyGeneInfo()

        #
        # Note July 27, 2019:
        #
        # mygene is unnable to map many of the ensembl gene ids to symbols;
        # using simpler static mapping tables taken from the R annotables package
        # until issue can be looked at more closely.
        #

        # Update: Aug 2020
        #
        # Since the effectiveness of mapping is highly dependent on the nature of the
        # input data, a better approach may be to support several methods (e.g.
        # mygene.info, annotables, and biomaRt), and allow the user to choose which
        # one they prefer... alternatively, each method could be tested and the mapping
        # with the highest success rate could be used)
        #

        # query mygene for gene identifiers
        #res = mg.querymany(dat.index,
        #                   scopes='{{ action.params["from"] }}', 
        #                   fields='{{ action.params["to"] }}', species='human',
        #                   as_dataframe=True)

        # temp: hard-coding until a more generalized approach can be implemented
        annot_file = os.path.join('{{ data_dir }}', 'annotations', 'annotables', 
                                  '{{ action.params["mapping"] }}.tsv.gz')

        mapping = pd.read_csv(annot_file, sep='\t')

        # create a mapping dictionary
        mapping = pd.Series(mapping['{{ action.params["to"] }}'].values, index=mapping['{{ action.params["from"] }}'].values).to_dict()

        # update indices
        dat = dat.set_index(dat.index.to_series().map(mapping).values)

        # drop genes that couldn't be mapped
        dat = dat[dat.index.notna()]

        # collapse multi-mapped genes using specified function
