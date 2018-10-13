"""
snakes template renderer
"""
import functools
import logging
import os
import sys
import yaml
from argparse import ArgumentParser
from jinja2 import Environment, ChoiceLoader, PackageLoader
from pkg_resources import resource_filename, Requirement

class SnakefileRenderer(object):
    """Base SnakefileRenderer class"""
    def __init__(self, config_filepath=None, **kwargs):
        self.config = None
        self.dataset_configs = {}

        self.output_file = 'Snakefile'

        self._setup_logger()

        self._load_config(config_filepath, **kwargs)
        self._validate_config()

    def _setup_logger(self):
        """Sets up logging environment"""
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(levelname)s] (%(asctime)s) - %(message)s', 
                                      datefmt='%Y-%m-%d %H:%M:%S')
        ch.setFormatter(formatter)
        root.addHandler(ch)

        logging.info("Initializing snakes")

    def _load_config(self, config_filepath, **kwargs):
        """Parses command-line arguments and loads snakes configuration."""
        # Load configuration
        parser = self._get_args()

        # get input arguments and convert to a dict
        cmdline_args = parser.parse_args()
        cmdline_args = dict((k, v) for k, v in list(vars(cmdline_args).items()) if v is not None)

        # If user specified a configuration filepath in uhe command, use that path
        if 'config' in cmdline_args:
            config_file = cmdline_args['config']

            if not os.path.isfile(config_file):
                logging.error("Invalid configuration path specified: %s" % config_file)
                sys.exit()

            logging.info("Using configuration: %s" % config_file)

        # Check for configuration file specified in the SnakefileRenderer constructor.
        elif config_filepath is not None:
            config_file = config_filepath
            if not os.path.isfile(config_file):
                logging.error("Invalid configuration path specified: %s" % config_file)
                sys.exit()

        # load main snakes configuration file
        with open(config_file) as fp:
            self.config = yaml.load(fp)

        # Update default arguments with user-specified settings
        self.config.update(cmdline_args)

        # Update with arguments specified to SnakefileRenderer constructor
        self.config.update(kwargs)

        # load dataset-specific config files
        for dataset_yaml in self.config['datasets']['features'] + self.config['datasets']['response']:
            self._load_dataset_config(dataset_yaml)

    def _load_dataset_config(self, input_yaml):
        """Loads a feature / response dataset config file and overides any global settings with
        dataset-specific ones."""
        # load dataset-specific config and filter
        cfg = yaml.load(open(input_yaml))

        # combine global and dataset-specific settings
        for param in ['filter', 'clustering', 'gene_sets']:
            if param in self.config:
                # use dataset-specific settings, if specified
                if param in cfg:
                    dataset_filters = cfg[param]
                    cfg[param] = self.config[param].copy()
                    cfg[param].update(dataset_filters)
                else:
                    # otherwise just use global config settings
                    cfg[param] = self.config[param].copy()

        self.dataset_configs[cfg['name']] = cfg

    def _validate_config(self):
        """Performs some basic check on config dict to make sure required settings are present."""
        # check filter settings
        for key, dataset_cfg in self.dataset_configs.items():
            # make sure filter type is specified
            if 'filter' not in dataset_cfg:
                continue

            for filter_name in dataset_cfg['filter']:
                if 'type' not in dataset_cfg['filter'][filter_name]:
                    msg = "Invalid coniguration! Missing 'type' for filter '{}'".format(filter_name)
                    raise Exception(msg)

    def _get_args(self):
        """Parses input and returns arguments"""
        parser = ArgumentParser(description='Dynamically generates Snakefiles for data integration and machine learning pipelines.')

        parser.add_argument('-c', '--config',
                            help=('Configuration filepath. (Will look for file named config.yml ' 
                                 'in current working directory, if none specified.)'))

        return parser

    def render(self):
        """Renders snakefile"""
        logging.info("Generating Snakefile...")

        # get snakefile jinja2 template
        loaders = [PackageLoader('snakes', 'templates'), 
                   PackageLoader('snakes', 'templates/aggregation'),
                   PackageLoader('snakes', 'templates/data'),
                   PackageLoader('snakes', 'templates/filters'),
                   PackageLoader('snakes', 'templates/transform'),
                   PackageLoader('snakes', 'templates/vis')]
        env = Environment(loader=ChoiceLoader(loaders), extensions = ['jinja2.ext.do'])
        template = env.get_template('Snakefile')

        # render template
        snakefile = template.render(config=self.config, datasets=self.dataset_configs)

        # save rendered snakefile to disk
        logging.info("Saving Snakefile to {}".format(self.output_file))
        
        with open(self.output_file, 'w') as fp:
            fp.write(snakefile)


