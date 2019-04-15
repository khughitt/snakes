        # cluster dataset
        clusters = clustering.hclust(dat, {{ action.num_clusters }})

        # add cluster column and store results
        dat['{{ action.col_name }}'] = clusters

