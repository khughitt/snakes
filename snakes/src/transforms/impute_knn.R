#!/bin/env Rscript
################################################################################
#
# Performs k-nearest neighbor imputation on a dataset
#
# Parameters
# ----------
#
################################################################################
library(VIM)

# parameters
params <- snakemake@params[['cfg']]

message('kNN')
print(params)
message(params)

# load data
dat <- read.csv(snakemake@input[[1]], row.names = 1)

ncols <- ncol(dat)

# impute missing values
dat <- kNN(dat, params)[, 1:ncols]

# save result
write.csv(dat, file=snakemake@output[[1]], quote = FALSE)
