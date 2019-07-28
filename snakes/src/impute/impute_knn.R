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
params <- snakemake@params[['args']]

# load data
dat <- read.csv(snakemake@input[[1]], row.names = 1)

# add data to function arguments
params[['data']] <- dat[, -1] 

message("Imputing missing data values...")

# impute missing values
imputed <- do.call(kNN, params)
dat[, -1] <- imputed[, 1:(ncol(dat) -1)]

# save result
write.csv(dat, file=snakemake@output[[1]], quote = FALSE)
