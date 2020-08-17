        # load gmt file
        gmt_file = '{{ action.params["gmt"] }}'

        if gmt_file.endswith('.gz'):
            fp = gzip.open(gmt_file, 'rt')
        else:
            fp = open(gmt_file, 'r')

        # iterate of gmt entries and construct a dictionary mapping from gene set names to lists
        # the genes they contain
        gsets = {}

        # gmt file column indices
        GENE_SET_NAME  = 0
        GENE_SET_START = 2

        # minimum number of genes required for a gene set to be used
        MIN_GENES = {{ action.params['min_size'] }}

        # iterate over gene sets, and those that meet the minimum size requirements
        for line in fp:
            # split line and retrieve gene set name and a list of genes in the set
            fields = line.rstrip('\n').split('\t')

            num_genes = len(fields) - 2

            if num_genes > MIN_GENES:
                gsets[fields[GENE_SET_NAME]] = fields[GENE_SET_START:len(fields)]

        fp.close()
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
        #dat.to_feather(output[0], compression='lz4')

