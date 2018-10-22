#!/bin/env Rscript
################################################################################
#
# Loads gene set GMT file and maps gene ids as needed
#
# Parameters
# ----------
#
################################################################################
library('annotables')
suppressMessages(library('dplyr'))

# gene ids
data_gid <- snakemake@params[['data_gid']]
gset_gid <- snakemake@params[['gset_gid']]

# vector of output lists
entries <- c()

# gmt file column indices
GENE_SET_NAME  = 1
GENE_SET_DESC  = 2
GENE_SET_START = 3

# iterate over gmt entries and map gene ids
for (line in readLines(snakemake@input[[1]])) {
  # split tab-delimited line
  gset_entry <- unlist(strsplit(line, '\t'))

  # map gene ids
  gset_ids <- gset_entry[GENE_SET_START:length(gset_entry)]

  indices <- match(gset_ids, grch37 %>% 
    pull (gset_gid))

  mapped_ids <- grch37[indices, ] %>%
    pull(data_gid)

  # add tab-delimited entry with new gene ids to output vector
  name_desc <- gset_entry[GENE_SET_NAME:GENE_SET_DESC]
  entries <- c(entries, paste(c(name_desc, mapped_ids), collapse = '\t'))
}

# write mapped gmt entries to file
fp <- file(snakemake@output[[1]])
writeLines(entries, fp)
close(fp)

