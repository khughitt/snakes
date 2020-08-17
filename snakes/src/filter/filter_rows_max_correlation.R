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
suppressMessages(library(arrow))
suppressMessages(library(caret))
suppressMessages(library(tibble))

options(stringsAsFactors = FALSE)

# parameters
params <- snakemake@params[['args']]

# load data
id_col <- colnames(dat)[1]

dat <- read_feather(snakemake@input[[1]]) %>%
  column_to_rownames(id_col)

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
ind <- findCorrelation(cor_mat, cutoff = params[['cutoff']], verbose = params[['verbose']])

if (length(ind) > 0) {
  message(sprintf("Removing %d / %d features with a correlation above %0.2f.",
                  length(ind), nrow(dat), params[['cutoff']]))
  dat <- dat[-ind, ]
} else {
  message('No correlated features detected!')
}

# move rownames back to column and save outpu
dat %>%
  rownames_to_column(id_col) %>%
  write_feather(snakemake@output[[1]], compression = 'lz4')
