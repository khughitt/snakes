"""
snakes template renderer
"""
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

        self.feature_configs = {}
        self.response_configs = {}

        self.output_file = 'Snakefile'

        self._setup_logger()
        logging.info("Initializing snakes")

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

        # load feature-specific config files
        for feature_yaml in self.config['features']:
            # load dataset-specific config and filter
            cfg = yaml.load(open(feature_yaml))

            # if global filter settings exist, use those as a base and update with
            # dataset-specific settings
            if 'filter' in self.config:
                if 'filter' in cfg:
                    dataset_filters = cfg['filter']
                    cfg['filter'] = self.config['filter'].copy()
                    cfg['filter'].update(dataset_filters)
                else:
                    cfg['filter'] = self.config['filter'].copy()

            self.feature_configs[cfg['name']] = cfg

        # load response-specific config files
        for response_yaml in self.config['response']:
            # load dataset-specific config and filter
            cfg = yaml.load(open(response_yaml))

            # if global filter settings exist, use those as a base and update with
            # dataset-specific settings
            if 'filter' in self.config:
                if 'filter' in cfg:
                    response_filters = cfg['filter']

                    cfg['filter'] = self.config['filter'].copy()
                    cfg['filter'].update(response_filters)
                else:
                    cfg['filter'] = self.config['filter'].copy()

            self.response_configs[cfg['name']] = cfg

    def _validate_config(self):
        """Performs some basic check on config dict to make sure required settings are present."""
        # check filter settings
        for key, feature_cfg in self.feature_configs.items():
            if 'filter' not in feature_cfg:
                continue

            # make sure filter type is specific
            for filter_name in feature_cfg['filter']:
                if 'type' not in feature_cfg['filter'][filter_name]:
                    msg = "Invalid coniguration! Missing 'type' for filter '{}'".format(filter_name)
                    raise Exception(msg)

        # check filter settings
        for key, response_cfg in self.response_configs.items():
            if 'filter' not in response_cfg:
                continue

            # make sure filter type is specific
            for filter_name in response_cfg['filter']:
                if 'type' not in response_cfg['filter'][filter_name]:
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
        snakefile = template.render(config=self.config, features=self.feature_configs,
                                    responses=self.response_configs)

        # save rendered snakefile to disk
        logging.info("Saving Snakefile to {}".format(self.output_file))
        
        with open(self.output_file, 'w') as fp:
            fp.write(snakefile)


