        # load gmt file
        entries = [x.rstrip('\n') for x in open('{{ action.params["gmt"] }}').readlines()]

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

        {% if action.params["gmt_key"] != action.params["data_key"] %}
        # map gene identifiers
        import mygene
        mg = mygene.MyGeneInfo()

        for gset_id in gsets:
            # query mygene.info 
            res = mg.querymany(gsets[gset_id], 
                                scopes='{{ action.params["gmt_key"] }}', 
                                fields='{{ action.params["data_key"] }}', species='human')
            {% if action.params["data_key"] == 'ensembl.gene' %}
            # parse mapped ensembl gene ids
            gsets[gset_id] = []
            
            for entry in res:
                # 1 to 1
                # { 'ensembl': { 'gene': 'xxx' } }
                if isinstance(entry['ensembl'], dict):
                    gsets[gset_id].append(entry['ensembl']['gene'])
                else:
                    # 1 to many
                    # { 'ensembl': [{ 'gene': 'xxx' }, { 'gene': 'yyy' }, ... ] }
                    gsets[gset_id] = gsets[gset_id] +[x['gene'] for x in entry['ensembl']] 
            {% else %}
            gsets[[gset_id]] = [x['{{ action.params["data_key"] }}'] for x in res]
            {% endif %}
        {% endif %}

        # apply function along gene sets and save output
        dat = gene_sets.gene_set_apply(dat, gsets, '{{ action.params["func"] }}')

        # update row names to include dataset, gene set, and function applied
        #dat.index = ["_".join([gset_id_prefix, gene_set, func]) for gene_set in dat.index]
        #dat.to_csv(output[0], index_label='gene_set_id')

