```
                 _
 ___ _ __   __ _| | _____  ___
/ __| '_ \ / _` | |/ / _ \/ __|
\__ \ | | | (_| |   <  __/\__ \
|___/_| |_|\__,_|_|\_\___||___/ v0.1 alpha

Data integration and machine learning pipeline built on Snakemake
```

# Table of contents

- [Development status](#development-status)
- [Overview](#overview)
- [Why Snakes](#why-snakes)
- [Scope](#scope)
- [How Snakes works](#how-snakes-works)
- [Example configuration](#example-configuration)
- [Installation](#installation)
- [Planned functionality](#planned-functionality)
- [Feedback / suggestions](#feedback--suggestions)

# Development status

**April 2019**:

Snakes is currently undergoing active development and is likely to change
significantly in the coming weeks. A more complete version of the targeted functionality is planned
for Spring/Summer 2019. In the meantime, if you are interested in contributing to the effort, feel
free to reach out!

# Overview

Snakes is a command-line tool, written in Python/R, which aims to provide a simple approach to
constructing pipelines for data integration and machine learning. Rather than re-implementing a
data pipeline framework from the ground up (for which there exist many really good ones such as
[Snakemake](https://snakemake.readthedocs.io/en/stable/), [Nextflow](https://www.nextflow.io/),
[Ruffus](http://www.ruffus.org.uk/), and [Luigi](https://github.com/spotify/luigi)), Snakes instead
seeks to provide an easy means to generate a pipeline using such a framework (specifically,
Snakemake), as well as providing some useful out-of-the-box functionality for assisting with data
integration, visualization, quality assurance, and machine learning.

# Why Snakes

As mentioned above, there are already a number of great frameworks for constructing data pipelines.
Why Snakes?

While each of the aforementioned frameworks provide a powerful set of tools for building modern
data science pipelines, they all generally share some limitations, which Snakes seeks to overcome.

The main features of Snakes include:

1. Simple configuration using [YAML](https://en.wikipedia.org/wiki/YAML) files.
2. [Out-of-the-box support](https://github.com/khughitt/snakes/tree/master/snakes/templates/actions) for common data transformation, visualization, machine learning, etc. 
   operations.
3. A modular design, making it easy to extend Snakes to support new operations.
4. Support for branching and integration / cross-data comparisons

Most pipeline frameworks, while extremely powerful and versatile, have a fair bit of a learning
curve. Moreover, since they are focused on the nuts-and-bolts of designing data workflows, they do
not include any built-in support for basic data science operations, and require a fair bit of
coding knowledge to successfully utilize.

The goal of Snakes is to provide a set of useful building blocks for data science pipelines, and a
simple means to stitch them together in order to construct a data science pipeline.

# Scope

Existing / planned functionality for snakes can be dividing into the following major categories:

1. Data filtering and transformations
2. Visualization and summarization
3. Integration and cross-dataset analysis
4. Incorporation of domain-specific knowledge
5. Feature selection and machine learning

The aim is this effort to produce software that is not tied to any specific research field, and is
useful across a wide range of problems. My background, however, is largely in bioinformatics and,
as such, the sorts of functionality that will be prioritized for inclusion will be guided by the
kinds of problems that I'm currently working on - in particular, integrative modeling for precision
medicine.

That said, the modular design of Snakes is aimed at making it straight-forward to add new
functionality, so users are welcome to submit pull requests with additional functionality, both
general, and domain-specific.

You can expect the functionality of Snakes to expand significantly in the coming months as code is
migrated from a prototype workflow into the new codebase.

# How Snakes works

Snakes uses the [Jinja2](http://jinja.pocoo.org/docs/2.10/) templating framework in order to
dynamically construct a static
[Snakefile](https://snakemake.readthedocs.io/en/stable/tutorial/basics.html) from one or more
YAML configuration files, which can then be executed by Snakemake.

# Example configuration

Below is a partial example set of config files for a hypothetical multi-omics bioinformatics
pipeline aimed at building models for predicting biomarkers associated with drug sensitivity.

The complete configuration can be found in the
[tests/settings](https://github.com/khughitt/snakes/tree/master/tests/settings) directory of the
repository.

Note that, as mentioned above, Snakes is currently under active development and is not considered
fully-functional at this time. The functionality described above _has_ been implemented in a
separate prototype, but still needs to be incorporated into the codebase proper.

In order to increase the re-usability of Snakes-based pipelines, config files may be split up into
several files including one main config (typically, "config.yml"), along with one or more
additional dataset-specific config files.

Below, an example main config file is shown, along with a sub-config file for processing a
transcriptomics ([RNA-Seq](https://en.wikipedia.org/wiki/RNA-Seq)) dataset. The config files for
the remaining datasets can be found in the `test/settings` directory.

**config.yml**

```yaml
################################################################################
#                  _             
#  ___ _ __   __ _| | _____  ___ 
# / __| '_ \ / _` | |/ / _ \/ __|
# \__ \ | | | (_| |   <  __/\__ \
# |___/_| |_|\__,_|_|\_\___||___/
#                               
# Example configuration
#
################################################################################

################################################################################
#
# General settings
#
################################################################################

# analysis name and version
name: 'test pipeline'
version: '1.0'

# output directory
output_dir: 'output'

# random seed
random_seed: 1

# output verbosity
verbose: true

################################################################################
#
# Data sources
#
################################################################################
data_sources:
  - 'tests/settings/features/rnaseq.yml'
  - 'tests/settings/features/cnv.yml'
  - 'tests/settings/features/variants.yml'
  - 'tests/settings/response/drug_screen.yml'
```

**rnaseq.yml**

```yaml
################################################################################
#
# RNA-Seq Example Configuration
#
################################################################################

# General
name: rnaseq
xid: ensgene
yid: sample_id

#
# Path to RNA-Seq count data
#
path: 'tests/data/features/rnaseq.csv'

# 
# RNA-Seq data processing steps
#
actions:
  - filter_columns_name_not_in:
      names: ['KMS20_JCRB']
  - filter_rows_var_gt:
      name: 'exclude_zero_variance'
      value: 0
  - filter_rows_sum_gt:
      name: 'filter_min_reads'
      value: 20
  - filter_rows_gene_biotype_in:
      name: 'filter_by_gene_type'
      gene_biotypes: ['protein_coding']
  - transform_cpm
  - transform_log2p
  - transform_zscore:
      name: 'transform_row_zscores'
      axis: 1
  - branch:
    - cluster_hclust:
        num_clusters: 4
```

# Installation

**Dependencies**

- [Python](https://www.python.org/) (3.4+)
- [Snakemake](https://snakemake.readthedocs.io/en/stable/)
- [Jinja2](http://jinja.pocoo.org/docs/2.10/)
- [PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [Numpy](http://www.numpy.org/)
- [Pandas](https://pandas.pydata.org/)
- [SciPy](https://www.scipy.org/)

**Optional dependencies**

Depending on the types of actions you wish to perform, the below dependencies are also recommended:

- [R](https://www.r-project.org/)
- [scikit-learn](https://scikit-learn.org/stable/)
- [statsmodels](https://www.statsmodels.org/stable/index.html)

**Installation using conda**

The recommended method for installing Snakes is to use [conda
environments](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands):

To begin, clone the snakes repo and `cd` into the directory:

```sh
git clone https://github.com/khughitt/snakes
cd snakes
```

Next, use the `conda env` command to create a new conda environment, specifying the list of
dependencies that should be installed:

```
conda create -n snakes \
  --file requirements.txt \
  --channel bioconda \
  --channel conda-forge
```

Finally, activate the new environment using:

```sh
conda activate snakes
```

To test out the new installation, you can try building the example workflow included with snakes,
using the command:

```
snakes -c tests/settings/config.yml
```

This should result in a `Snakefile` being generated in your current directory. This can be executed
by simply calling snakemake:

```sh
snakemake
```

# Planned functionality

Most of the below have already been implemented prototype R version of software. Expect them to be
added in the coming months, with a target "release date" for the major functionality of
Spring/Summer 2019.

- [ ] Dimension reduction methods (PCA, NMF, t-SNE, UMAP)
- [ ] Visualization
- [ ] Additional normalization methods
- [ ] Additional clustering methods
- [ ] Pivoting transformations
- [ ] Summarization / RMarkdown report generation
- [ ] Outlier detection
- [ ] Batch adjustment
- [ ] Pathway- and gene set-based feature aggregation
- [ ] Feature selection
- [ ] Cross-data correlation
- [ ] Model training and cross-validation
- [ ] Singularity container support
- [ ] Support for working with additional / raw data formats
- [ ] Documentation

# Feedback / suggestions

Feedback and suggestions are always welcome. Feel free to [reach out](mailto:keith.hughitt@nih.gov)
if you have ideas for the project, or would like to become involved.

