################################################################################
#'
#' Filters a dataset to remove correlated rows. For each pair of rows with a 
#' pairwise correlation higher than the specific cutoff, one will be removed at
#' random.
#'
#' The findCorrelation method from the caret package is used to detect correlated
#' features.
#'
#' Parameters
#' ----------
#' cutoff: float
#'   maximum correlation between features to allow (default: 0.9)
#' cor_method: str
#'   method to use for building the correlation matrix (default: cor)
#'   accepted options: [cor|wgcna]
#' nthreads: int
#'   number of threads to use. applies to wgcna::cor method only (default: 0)
#' use: str
#'   how to handle missing data (default: 'pairwise.complete.obs')
#' verbose: bool
#'   whether or not to display verbose output (default: false)
#'
################################################################################
suppressMessages(library(caret))

options(stringsAsFactors = FALSE)

# parameters
params <- snakemake@params[['args']]

# load data
dat <- read.csv(snakemake@input[[1]], row.names = 1)

# determine correlation method and arguments to use
if (params[['cor_method']] == 'cor') {
  cor_func <- cor
  cor_args <- params[c('use')]
} else if (params[['cor_method']] == 'wgcna') {
  suppressMessages(library(WGCNA))
  cor_func <- WGCNA::cor
  cor_args <- params[c('use')]
  cor_args$nThreads <- params$nthreads
} else {
  stop("Invalidation correlation method specified! Valid options are: cor|wgcna.")
}

# add data to arguments; transpose so that correlated rows are detected
cor_args$x <- t(dat)

# construct pairwise correlation matrix
cor_mat <- do.call(cor_func, cor_args)

# detect and remove correlated features
ind <- caret::findCorrelation(cor_mat, cutoff = params[['cutoff']], 
                              verbose = params[['verbose']])

if (length(ind) > 0) {
  message(sprintf("Removing %d / %d features with a correlation above %0.2f.",
                  length(ind), nrow(dat), params[['cutoff']]))
  dat <- dat[-ind, ]
} else {
  message('No correlated features detected!')
}

# save result
write.csv(dat, file=snakemake@output[[1]], quote = TRUE)
