============
User's Guide
============

Overview
--------

TODO

Installation
------------

TODO

Configuration
-------------

Main configuration
##################

In order to run `snakes`, a valid `YAML <http://yaml.org/>`_ configuration file must be provided.
An example config file (`config.example.yml`) is provided in the `tests/settings` directory. This
configuration file is used to specify the globa pipeline parameters to use as well as the locations 
of dataset-specific config files. Dataset-specific configuration is described later in the 
:ref:`dataset-config` section.

Below is an example `config.yml` which, in addition to including general settings and global
filters and aggregation functions which should be applied to all features, also links to four 
additional dataset-specific config files.

.. code-block:: yaml

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

   ################################################################################
   #
   # Data sources
   #
   ################################################################################
   datasets:
      features:
         - 'tests/settings/features/rnaseq.yml'
         - 'tests/settings/features/cnv.yml'
         - 'tests/settings/features/variants.yml'
      response:
         - 'tests/settings/response/drug_screen.yml'

   metadata:
      samples: 'tests/data/metadata/sample_metadata.csv'
      response: 'tests/data/metadata/drug_metadata.csv'

   ################################################################################
   #
   # Global filters
   #
   ################################################################################
   filters:
      exclude_columns:
         type: 'exclude_columns'
         columns_to_exclude: ['KMS20_JCRB']
      zero_variance:
         type: 'row_var_above'
         value: 0

   ################################################################################
   #
   # Clustering
   #
   ################################################################################
   clustering:
      hclust:
         num_clusters: 4
         funcs: ['sum', 'var']

   ################################################################################
   #
   # Gene sets
   #
   ################################################################################
   gene_sets:
      go:
         gene_id: 'entrez'
         gmts:
            - 'tests/data/gene_sets/go.gmt'
         funcs: ['max', 'median']


The main required parameters are:

- `name` - name of the pipeline
- `version` - a version string to be used to keep track of multiple versions of a pipeline
- `output_dir` - the base output directory to save pipeline outputs to
- `datasets` - locations of feature and response :ref:`dataset-specific config files <dataset-config>`.

.. _dataset-config:

Dataset configuration
#####################

TODO: describe expected format of data / options for specifying alternatives..
