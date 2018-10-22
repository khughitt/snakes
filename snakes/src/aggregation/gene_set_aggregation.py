#!/bin/env python
"""
Python code for gene set aggregation

Note 2018/10/22: This is currently not being used in favor of R code which can easily convert
gene id's on-the-fly.
"""
# load dataset
df = pd.read_csv(input[0], index_col=0)

# load gmt file
entries = [x.rstrip('\n') for x in open('{{ gmt }}').readlines()]

# gmt file column indices
GENE_SET_NAME  = 0
GENE_SET_START = 2

# iterate of gmt entries and construct a dictionary mapping from gene set names to lists
# the genes they contain
gene_sets = {}

for entry in entries:
    # split line and retrieve gene set name and a list of genes in the set
    fields = entry.split('\t')

    gene_sets[fields[GENE_SET_NAME]] = fields[GENE_SET_START:len(fields)]

# iterate over functions and create one output for each function
fxns = {{ gene_set_params['fxns'] }}

for i in range(len(fxns)):
    fxn = fxns[i]

    # validate function (currently, only numpy methods supported)
    if not hasattr(np, fxn):
        raise("Invalid gene set aggegration function specified!")

    # list to store aggegration result tuples; will be used to construct a DataFrame
    rows = []

    # iterate over gene sets and apply function
    for gene_set, genes in gene_sets.items():
        rows.append(tuple(df.filter(genes, axis=0).apply(getattr(np, fxn))))

    # extend row id to include datatype, gmt, and aggregation fxn
    gene_set_ids = ["_".join(['{{dataset_name}}', '{{gmt_name | to_rule_name}}', gene_set, fxn]) for gene_set in gene_sets.keys()]

    pd.DataFrame(rows, index=gene_set_ids, columns=df.columns).to_csv(output[i], index_label='gene_set_id')
