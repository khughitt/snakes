#!/bin/env python
"""
Generate snakes test datasets

This script generates several small datasets for use with testing snakes. Each dataset
includes 10 columns corresponding to samples. Below are the fake datasets generated along with
the dataset dimensions and what each dimension represents.

    1. rnaseq (50 genes x 10 samples)
    2. cnv (50 genes x 10 samples)
    3. response (5 drugs x 10 samples)

Additionally, a GMT annotation file containing five fake gene sets is also created, as well as
sample and drug metadata tables.
"""
import numpy as np
import pandas as pd
import random

# set random seeds
random.seed(0)
np.random.seed(0)

# data dimensions
num_samples = 10

# sample and row ids
sample_ids = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']

rnaseq_gene_ids  = ['gene{:02d}'.format(x) for x in range(50)]
cnv_gene_ids     = ['gene{:02d}'.format(x) for x in range(35, 65)]
all_gene_ids     = list(set(rnaseq_gene_ids).union(cnv_gene_ids))
all_gene_ids.sort()

drug_ids = ['drug{:02d}'.format(x) for x in range(5)]

# generate fake data and save to disk

# RNA-Seq
pd.DataFrame(np.random.randint(0, 10000, size=(50, num_samples)),
             index = rnaseq_gene_ids, columns = sample_ids).to_csv('data/rnaseq.csv')

# CNV
pd.DataFrame(np.round(np.random.normal(size=(30, num_samples)), 2),
             index = cnv_gene_ids, columns = sample_ids).to_csv('data/cnv.csv')

# Drug AC-50
pd.DataFrame(np.round(np.random.lognormal(mean=0, sigma=0.25, size = (5, num_samples)) * 50, 2),
             index = drug_ids, columns = sample_ids).to_csv('data/ac50.csv')

# Sample metadata
pd.DataFrame({'var1': np.random.choice([0, 1], 10),
              'var2': np.random.choice(['a', 'b', 'c'], 10)},
              index=sample_ids).to_csv('data/sample_metadata.csv')

# drug metadata
pd.DataFrame({'varA': np.random.choice(['A', 'B', 'C'], 5)},
              index=drug_ids).to_csv('data/drug_metadata.csv')

# Gene sets
with open('data/gene_sets.gmt', 'w') as fp:
    fp.write('\t'.join(['GENE_SET_1', 'description 1'] + random.sample(rnaseq_gene_ids, 10)))
    fp.write('\t'.join(['GENE_SET_2', 'description 2'] + random.sample(rnaseq_gene_ids, 5)))
    fp.write('\t'.join(['GENE_SET_2', 'description 2'] + random.sample(all_gene_ids, 20)))

