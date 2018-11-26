#!/bin/env Rscript
################################################################################
#
# Performs hierarchical clustering on a dataset and applies a function to each
# resulting cluster to generate a new dataset.
#
# Parameters
# ----------
# cor_method: Correlation method to use (default: Pearson correlation)
# hclust_method: Hierarchical clustering method to use (default: 'average')
# cutree_method: Tree cut method to use (default: cutree)
# k: Number of clusters to create.
# h: Height to cut dendrogram.
#
################################################################################
suppressMessages(library(flashClust))

# parameters
params <- snakemake@params[['clust_params']]

# load data
mat <- as.matrix(read.csv(snakemake@input[[1]], row.names = 1))

# compute correlation matrix
cor_mat <- cor(t(mat))

# perform hierarchical clustering
hc <- flashClust(as.dist(1 - abs(cor_mat)), method='average')

# divide hierarchical clustering dendrogram into clusters
clusters <- cutree(hc, k=params$num_clusters)

# iterate over functions/statistics to be applied to each cluster 
for (i in seq_along(params$funcs)) {
  # apply function cluster-wise to original data matrix
  func <- params$funcs[i]

  cluster_ids <- factor(sprintf('%s-hclust-%s-%03d', snakemake@params$dat_name, func, clusters))

  res <- aggregate(mat, list(cluster_id = cluster_ids), get(func))

  # save result
  write.csv(res, file=snakemake@output[[i]], quote = FALSE, row.names = FALSE)
}
