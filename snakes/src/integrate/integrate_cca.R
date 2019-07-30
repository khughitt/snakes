################################################################################
#
# Canonical Correlation Analysis (CCA)
#
################################################################################
suppressMessages(library(readr))
suppressMessages(library(PMA))

set.seed(1)

# load datasets
x <- t(read.csv(snakemake@input[[1]], row.names = 1))
y <- t(read.csv(snakemake@input[[2]], row.names = 1))

# reorder columns to match
x <- x[rownames(y), ]

# Perform CCA projection and keep two first canonical vectors
res <- CCA.permute(x, y, trace = TRUE, standardize = TRUE, niter = 5, nperm = 35)

# TEMP / placeholder
write_csv(res$pvals)
