################################################################################
#
# Canonical Correlation Analysis (CCA)
#
# (IN DEVELOPMENT)
#
################################################################################
suppressMessages(library(arrow))
suppressMessages(library(PMA))

set.seed(1)

# load datasets
X <- read_feather(snakemake@input[[1]])

X <- X %>%
  column_to_rownames(colnames(X)[1]) %>%
  as.matrix() %>%
  t()

Y <- read_feather(snakemake@input[[2]])

Y <- Y %>%
  column_to_rownames(colnames(Y)[1]) %>%
  as.matrix() %>%
  t()

# reorder columns to match
X <- X[rownames(Y), ]

# Perform CCA projection and keep two first canonical vectors
res <- CCA.permute(X, Y, trace = TRUE, standardize = TRUE, niter = 5, nperm = 35)

# TEMP / placeholder
write_feather(res$pvals, compression = 'lz4')
