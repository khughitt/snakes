################################################################################
#
# Performs k-nearest neighbor imputation on a dataset
#
# Parameters
# ----------
#
################################################################################
suppressMessages(library(VIM))
suppressMessages(library(arrow))

# parameters
params <- snakemake@params[['args']]

# load data
dat <- read_feather(snakemake@input[[1]])

# add data to function arguments
params[['data']] <- as.data.frame(dat[, -1])

message("Imputing missing data values...")

# impute missing values
imputed <- do.call(kNN, params)

# kNN returns a dataframe that is twice as wide as the input data;
# the first half contains the imputed values and the right half
# is a boolean mask indicating which values were imputed
dat[, -1] <- imputed[, 1:(ncol(dat) - 1)]

# save result
write_feather(dat, snakemake@output[[1]], compression = 'lz4')

sessionInfo()
