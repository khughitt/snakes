        # cluster dataset
        clusters = clustering.hclust(dat, {{ action.params.num_clusters }})

        # add cluster column and store results
        dat['{{ action.params.col_name }}'] = clusters

