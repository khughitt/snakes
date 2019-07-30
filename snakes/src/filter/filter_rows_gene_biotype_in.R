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
params <- snakemake@params[['args']]

# load data
dat <- read.csv(snakemake@input[[1]], row.names = 1)

# query biomaRt for gene biotype
ensembl = useMart("ensembl", dataset = "hsapiens_gene_ensembl")
genes <- getBM(attributes = c("ensembl_gene_id", "gene_biotype"), mart = ensembl)

# get a list of genes matching specified type(s)
include_genes <- genes[genes$gene_biotype %in% params['gene_biotypes'], ]$ensembl_gene_id

dat <- dat[rownames(dat) %in% include_genes, ]

# save result
write.csv(dat, file=snakemake@output[[1]], quote = TRUE)
