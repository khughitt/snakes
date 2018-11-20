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
    def _get_default_dataset_config():
        """Returns a dictionary of the default arguments associated with a dataset config entry"""
        return {
            'type': 'numeric',
            'role': 'feature',
            'xid': 'x',
            'yid': 'y',
            'sep': ',',
            'index_col': 0
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

        # load dataset-specific config files
        for dataset_yaml in (self.main_config['datasets']['features'] +
                             self.main_config['datasets']['response']):
            self._load_dataset_config(dataset_yaml)

    def _load_dataset_config(self, input_yaml):
        """Loads a feature / response dataset config file and overides any global settings with
        dataset-specific ones."""
        # default dataset settings
        cfg = self._get_default_dataset_config()

        # load dataset-specific configuration
        cfg.update(yaml.load(open(input_yaml)))

        # each feature dataset carries its own dataset-specific settings which get
        # applied along with any global filtering, etc. settings specified in the parent config.
        # In cases where a setting is specified in both the global config, and the dataset-specific
        # one, the dataset-specific options take priority.
        if cfg['role'] == 'feature':
            for param in ['filters', 'transforms', 'clustering', 'gene_sets']:
                if param in self.main_config:
                    # use dataset-specific settings, if specified
                    if param in cfg:
                        dataset_params = cfg[param]
                        cfg[param] = self.main_config[param].copy()
                        cfg[param].update(dataset_params)
                    else:
                        # otherwise just use global config settings
                        cfg[param] = self.main_config[param].copy()

        # set default quantile / value function args for filters
        if 'filters' in cfg:
            for filter_cfg in cfg['filters']:
                if 'quantile' not in cfg['filters'][filter_cfg]:
                    cfg['filters'][filter_cfg]['quantile'] = None
                if 'value' not in cfg['filters'][filter_cfg]:
                    cfg['filters'][filter_cfg]['value'] = None

        self.dataset_configs[cfg['name']] = cfg

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
        # required parameters for all dataset configuration
        shared_dataset_reqs = ['name', 'path']

        # data type specific required params
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
        for transform_name in transforms:
            # check for require parameter: type
            if 'type' not in transforms[transform_name]:
                msg = ("Invalid coniguration! Missing 'type' for transform "
                       "'{}'").format(transform_name)
                raise Exception(msg)

            # check to make sure a valid transform type is specified
            transform_type = transforms[transform_name]['type']
            template_filename = transform_type + '.snakefile'

            if template_filename not in os.listdir(os.path.join(template_dir,
                                                                'transforms')):
                msg = ("Invalid coniguration! Unknown transform type: "
                       "'{}'").format(transform_type)
                raise Exception(msg)

    def _validate_filter_config(self, filters, template_dir):
        """Validates filters portion of snakes config"""
        # for each filter and transform, make sure a valid type is specified
        for filter_name in filters:
            # check for require parameter: type
            if 'type' not in filters[filter_name]:
                msg = ("Invalid coniguration! Missing 'type' for filter "
                       "'{}'").format(filter_name)
                raise Exception(msg)

            # check to make sure a valid filter type is specified
            filter_type = filters[filter_name]['type']
            template_filename = filter_type + '.snakefile'

            if template_filename not in os.listdir(os.path.join(template_dir, 'filters')):
                msg = "Invalid coniguration! Unknown filter type: '{}'".format(filter_type)
                raise Exception(msg)


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
        env = Environment(loader=ChoiceLoader(loaders), extensions=['jinja2.ext.do'])

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
