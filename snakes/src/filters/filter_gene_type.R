#!/bin/env Rscript
################################################################################
#
# Filters a dataset containing gene entries based on gene type.
#
# Parameters
# ----------
#
################################################################################
library(biomaRt)

# parameters
params <- snakemake@params[['filter_params']]

# load data
dat <- read.csv(snakemake@input[[1]], row.names = 1)

# query biomaRt for gene biotype
ensembl = useMart("ensembl", dataset = "hsapiens_gene_ensembl")
genes <- getBM(attributes = c("ensembl_gene_id", "gene_biotype"), mart = ensembl)

# get a list of genes matching specified type(s)
coding_genes <- genes[genes$gene_biotype %in% params['include_gene_types'], ]$ensembl_gene_id

dat <- dat[rownames(dat) %in% coding_genes, ]

# save result
write.csv(dat, file=snakemake@output[[1]], quote = FALSE, row.names = FALSE)
