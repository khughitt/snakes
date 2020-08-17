#!/bin/env Rscript
################################################################################
#
# Filters a dataset containing gene entries based on gene type.
#
# Parameters
# ----------
# gene_biotype: list of biomaRt gene biotypes to allow (e.g. "protein coding")
# key_type: gene identifier type, as used in biomaRt (e.g. "ensembl_gene_id" or
# "external_gene_name") 
#
################################################################################
library(biomaRt)

# parameters
key_type      <- snakemake@params$key_type
gene_biotypes <- snakemake@params$gene_biotypes

# load data
dat <- read.csv(snakemake@input[[1]], row.names = 1)

# query biomaRt for gene biotype
ensembl = useMart("ensembl", dataset = "hsapiens_gene_ensembl")

# query attributes
genes <- getBM(attributes = c(key_type, "gene_biotype"), mart = ensembl)

# get a list of genes matching specified type(s)
include_genes <- genes[genes$gene_biotype %in% gene_biotypes, ][, key_type]

dat <- dat[rownames(dat) %in% include_genes, ]

# check to make sure non-zero result returned
if (nrow(dat) == 0) {
  stop("No genes remaining after filtering by biotype! ",
       "Are you sure you specified the correct key type?")
}

# save result
write.csv(dat, file = snakemake@output[[1]], quote = TRUE)
