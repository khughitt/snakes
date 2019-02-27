    run:
        # load dataset
        df = pd.read_csv(input[0], index_col=0)

        # cluster dataset
        clusters = clustering.hclust(df, {{ action.num_clusters }})

        # add cluster column and store results
        df['{{ action.col_name }}'] = clusters

        df.to_csv(output[0])

