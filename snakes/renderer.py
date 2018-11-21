"""
snakes template renderer
"""
import datetime
import logging
import os
import re
import sys
from argparse import ArgumentParser

import yaml
from jinja2 import Environment, ChoiceLoader, PackageLoader
from pkg_resources import resource_filename

class SnakefileRenderer():
    """Base SnakefileRenderer class"""
    def __init__(self, config_filepath=None, **kwargs):
        self.main_config = None
        self.dataset_configs = {}

        self.output_file = 'Snakefile'

        self._setup_logger()

        self._load_config(config_filepath, **kwargs)
        self._validate_config()

    @staticmethod
    def _setup_logger():
        """Sets up logging environment"""
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        log_handle = logging.StreamHandler(sys.stdout)
        log_handle.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(levelname)s] (%(asctime)s) - %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        log_handle.setFormatter(formatter)
        root.addHandler(log_handle)

        logging.info("Initializing snakes")

    @staticmethod
    def _get_default_config():
        """Returns a dictionary of default settings."""
        return {
            # general
            'output_dir': 'output',

            # development mode options
            'dev_mode': False,
            'dev_mode_subsample_ratio': 0.05,

            # random seed
            'random_seed': 1,

            # metadata
            'metadata': {},

            # dataset filters
            'filters': {},

            # dataset transforms
            'transforms': {},

            # clustering
            'clustering': {},

            # gene sets
            'gene_sets': {},

            # software settings
            'software': {
                'biomart': {
                    'mart': 'ensembl',
                    'dataset': 'hsapiens_gene_ensembl'
                }
            }
        }

    @staticmethod
    def _get_default_feature_config():
        """Returns a dictionary of the default arguments associated with a feature dataset config 
           entry"""
        return {
            'type': 'numeric',
            'role': 'feature',
            'xid': 'x',
            'yid': 'y',
            'sep': ',',
            'index_col': 0,
            'filters': {},
            'transforms': {},
            'clustering': {},
            'gene_sets': {}
        }

    @staticmethod
    def _get_default_response_config():
        """Returns a dictionary of the default arguments associated with a response dataset config
           entry"""
        return {
            'type': 'numeric',
            'role': 'response',
            'xid': 'x',
            'yid': 'y',
            'sep': ',',
            'index_col': 0,
            'filters': {},
            'transforms': {}
        }

    def _load_config(self, config_filepath, **kwargs):
        """Parses command-line arguments and loads snakes configuration."""
        # get command-line arguments and convert to a dict
        parser = self._get_args()
        cmdline_args = parser.parse_args()
        cmdline_args = dict((k, v) for k, v in list(vars(cmdline_args).items()) if v is not None)

        # If user specified a configuration filepath on the command-line, use that path
        if 'config' in cmdline_args:
            config_file = cmdline_args['config']
        elif config_filepath is not None:
            # otherwise use filepath specified in constructor, if specified
            config_file = config_filepath
        else:
            # finally, check for config file in current working directory
            config_file = 'config.yml'

        if not os.path.isfile(config_file):
            logging.error("Invalid configuration path specified: %s", config_file)
            sys.exit()

        logging.info("Using configuration: %s", config_file)

        # get default configuration options
        self.main_config = self._get_default_config()

        # load main snakes configuration file
        with open(config_file) as fp:
            self.main_config.update(yaml.load(fp))

        # Update default arguments with user-specified settings
        self.main_config.update(cmdline_args)

        # Update with arguments specified to SnakefileRenderer constructor
        self.main_config.update(kwargs)

        # Store filepath of config file used
        self.main_config['config_file'] = os.path.abspath(config_file)

        # check to make sure require dataset elements have been specified
        if 'datasets' not in self.main_config:
            raise Exception("Invalid coniguration! Missing required parameter 'datasets'")
        elif 'features' not in self.main_config['datasets']:
            raise Exception("Invalid coniguration! Missing required datasets parameter 'features'")
        elif 'response' not in self.main_config['datasets']:
            raise Exception("Invalid coniguration! Missing required datasets parameter 'response'")

        # parse feature and filter sections of main config
        self.main_config['filters'] = self._parse_filter_config(self.main_config['filters'])
        self.main_config['transforms'] = self._parse_transform_config(self.main_config['transforms'])

        # load feature dataset configs
        for yml in self.main_config['datasets']['features']:
            self._load_feature_config(yml)

        # load response dataset config
        self._load_response_config(yml)

    def _load_feature_config(self, input_yaml):
        """Loads a feature / response dataset config file and overides any global settings with
        dataset-specific ones."""
        # default dataset settings
        cfg = self._get_default_feature_config()

        # load dataset-specific configuration
        cfg.update(yaml.load(open(input_yaml)))

        # parse filter and transform sections of configs and set appropriate defaults
        cfg['filters'] = self._parse_filter_config(cfg['filters'])
        cfg['transforms'] = self._parse_transform_config(cfg['transforms'])

        # each feature dataset carries its own dataset-specific settings which get
        # applied along with any global filtering, etc. settings specified in the parent config.
        # In cases where a setting is specified in both the global config, and the dataset-specific
        # one, the dataset-specific options take priority.
        for param in ['filters', 'transforms', 'clustering', 'gene_sets']:
            if param in self.main_config:
                dataset_params = cfg[param]
                cfg[param] = self.main_config[param].copy()
                cfg[param].update(dataset_params)

        self.dataset_configs[cfg['name']] = cfg

    def _load_response_config(self, input_yaml):
        """Loads a response dataset config file and overides any global settings with
        dataset-specific ones."""
        # default dataset settings
        cfg = self._get_default_response_config()

        # load dataset-specific configuration
        cfg.update(yaml.load(open(input_yaml)))

        # parse filter and transform sections of configs and set appropriate defaults
        cfg['filters'] = self._parse_filter_config(cfg['filters'])
        cfg['transforms'] = self._parse_transform_config(cfg['transforms'])

        self.dataset_configs[cfg['name']] = cfg

    def _parse_transform_config(self, transforms):
        """Loads transforms section of global or dataset-specific config"""
        # if transforms specified using a list, convert to dict
        if isinstance(transforms, list):
            transforms = {transform: {'name': transform} for transform in transforms}

        # list to keep track of names used; if multiple versions of the same transform are applied,
        # a number will be suffixed to the name to avoid rule collisions
        used_names = []

        # set default transform name parameter, if not specified
        for transform in transforms:
            # if no specific name has been given to the transform entry, default to the name of
            # the transform itself
            if 'name' not in transforms[transform]:
                transforms[transform]['name'] = transform

            # if type of transform has already been included, append a number to the name
            if transforms[transform]['name'] in used_names:
                # number of times transform has been used so far
                i = len([x for x in used_names if x.startswith(transforms[transform]['name'])]) + 1

                transforms[transform]['name'] = transforms[transform]['name'] + "_" + str(i)

            # update used name list
            used_names.append(transforms[transform]['name'])

        return transforms

    def _parse_filter_config(self, filters):
        """Loads filters section of global or dataset-specific config"""
        # if filters specified using a list, convert to dict
        if isinstance(filters, list):
            filters = {filter_: {'name': filter_} for filter_ in filters}

        # list to keep track of names used; if multiple versions of the same filters are applied,
        # a number will be suffixed to the name to avoid rule collisions
        used_names = []

        # set default filter name parameter, if not specified
        for filter_ in filters:
            # if no specific name has been given to the filter entry, default to the name of
            # the filter itself
            if 'name' not in filters[filter_]:
                filters[filter_]['name'] = filter_

            # if type of filter has already been included, append a number to the name
            if filters[filter_]['name'] in used_names:
                # number of times filter has been used so far
                i = len([x for x in used_names if x.startswith(filters[filter_]['name'])]) + 1

                filters[filter_]['name'] = filters[filter_]['name'] + "_" + str(i)

            # update used name list
            used_names.append(filters[filter_]['name'])

            # set default filter value and quantile parameters, if not specified
            if 'quantile' not in filters[filter_]:
                filters[filter_]['quantile'] = None
            if 'value' not in filters[filter_]:
                filters[filter_]['value'] = None

        return filters

    def _validate_config(self):
        """Performs some basic check on config dict to make sure required settings are present."""
        #  check for required parameters in main config
        required_params = ['name', 'version', 'datasets']

        for param in required_params:
            if param not in self.main_config:
                msg = "Invalid coniguration! Missing required parameter '{}'".format(param)
                raise Exception(msg)

            self._validate_dataset_configs()

    def _validate_dataset_configs(self):
        """Validate dataset-specific configurations"""
        # required parameters for all types of data
        shared_dataset_reqs = ['name', 'path']

        # data type-specific required parameters
        specific_dataset_reqs = {
            'dose_response_curves': ['sample_id', 'compound_id', 'response_var']
        }

        # base template directory
        template_dir = os.path.abspath(resource_filename(__name__, 'templates'))

        # check dataset-specific settings
        for key, dataset_cfg in self.dataset_configs.items():
            # make sure required parameters have been specified
            required_params = shared_dataset_reqs

            if key in specific_dataset_reqs.keys():
                required_params = required_params + specific_dataset_reqs[key]

            for param in required_params:
                if param not in dataset_cfg:
                    msg = ("Invalid coniguration! Missing required parameter '{}' "
                           "for dataset '{}'").format(param, key)
                    raise Exception(msg)

            if 'filters' in dataset_cfg:
                self._validate_filter_config(dataset_cfg['filters'], template_dir)

            if 'transforms' in dataset_cfg:
                self._validate_transform_config(dataset_cfg['transforms'], template_dir)

    def _validate_transform_config(self, transforms, template_dir):
        """Validates transformations portion snakes config"""
        for transform in transforms:
            # check to make sure a valid transform type is specified
            template = transform + '.snakefile'

            if template not in os.listdir(os.path.join(template_dir, 'transforms')):
                msg = "Invalid coniguration! Unknown transform type: '{}'".format(transform)
                raise Exception(msg)

    def _validate_filter_config(self, filters, template_dir):
        """Validates filters portion of snakes config"""
        # for each filter and transform, make sure a valid type is specified
        for filter_ in filters:
            # check to make sure a valid filter type is specified
            template = filter_ + '.snakefile'

            if template not in os.listdir(os.path.join(template_dir, 'filters')):
                raise Exception("Invalid coniguration! Unknown filter type: '{}'".format(filter_))

    def _get_args(self):
        """Parses input and returns arguments"""
        parser = ArgumentParser(description='Dynamically generates Snakefiles for data '
                                            'integration and machine learning pipelines.')

        parser.add_argument('-c', '--config',
                            help=('Configuration filepath. (Will look for file named config.yml '
                                  'in current working directory, if none specified.)'))

        return parser

    def render(self):
        """Renders snakefile"""
        logging.info("Generating Snakefile...")

        # template search paths
        loaders = [PackageLoader('snakes', 'templates'),
                   PackageLoader('snakes', 'templates/aggregation'),
                   PackageLoader('snakes', 'templates/data'),
                   PackageLoader('snakes', 'templates/filters'),
                   PackageLoader('snakes', 'templates/transform'),
                   PackageLoader('snakes', 'templates/vis')]

        # get jinaj2 environment
        env = Environment(loader=ChoiceLoader(loaders), trim_blocks=True, lstrip_blocks=True,
                          extensions=['jinja2.ext.do'])

        #
        # define custom jinja2 filters
        #
        def basename_no_ext(filepath):
            """Strips directories and extension from a filepath"""
            return os.path.basename(os.path.splitext(filepath)[0])

        def replace_filename(filepath, filename):
            """Repaces the filename portion of a filepath"""
            return os.path.join(os.path.dirname(filepath), filename)

        def to_rule_name(rule):
            """Takes a string and replaces characters that aren't allowed in snakemake rule names
            with underscores"""
            return re.sub(r"[^\w]", "_", rule)

        env.filters['basename']         = os.path.basename
        env.filters['basename_no_ext']  = basename_no_ext
        env.filters['replace_filename'] = replace_filename
        env.filters['to_rule_name']     = to_rule_name

        # get snakefile jinja2 template
        template = env.get_template('Snakefile')

        # root snakes script directory
        script_dir = os.path.abspath(resource_filename(__name__, 'src'))

        # render template
        snakefile = template.render(config=self.main_config, datasets=self.dataset_configs,
                                    date_str=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    script_dir=script_dir)

        # save rendered snakefile to disk
        logging.info("Saving Snakefile to %s", self.output_file)

        with open(self.output_file, 'w') as file_handle:
            file_handle.write(snakefile)
