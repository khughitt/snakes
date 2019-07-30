################################################################################
#
# Performs k-nearest neighbor imputation on a dataset
#
# Parameters
# ----------
#
################################################################################
suppressMessages(library(VIM))
suppressMessages(library(readr))

# parameters
params <- snakemake@params[['args']]

# load data
dat <- read_csv(snakemake@input[[1]], col_types = cols())

# add data to function arguments
params[['data']] <- as.data.frame(dat[, -1])

message("Imputing missing data values...")

save(params, dat, file='~/tmp.rda')

# impute missing values
imputed <- do.call(kNN, params)

# kNN returns a dataframe that is twice as wide as the input data;
# the first half contains the imputed values and the right half
# is a boolean mask indicating which values were imputed
dat[, -1] <- imputed[, 1:(ncol(dat) - 1)]

# save result
write_csv(dat, snakemake@output[[1]])

sessionInfo()
