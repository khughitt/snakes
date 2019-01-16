"""
snakes template renderer
"""
import datetime
import logging
import pprint
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
        self.feature_configs = {}
        self.response_config = None

        self.output_file = 'Snakefile'

        self._setup_logger()

        self._conf_dir = os.path.abspath(resource_filename(__name__, 'conf'))
        self._template_dir = os.path.abspath(resource_filename(__name__, 'templates'))

        self._load_config(config_filepath, **kwargs)

    @staticmethod
    def _setup_logger():
        """Sets up logging environment"""
        root = logging.getLogger()
        root.setLevel(logging.INFO)

        log_handle = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('[%(levelname)s] (%(asctime)s) - %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        log_handle.setFormatter(formatter)
        root.addHandler(log_handle)

        logging.info("Initializing snakes")

    def _get_settings(self, which='defaults', section='main', target=None):
        """Returns a dictionary of default or required settings for a specified config section"""
        # load default/required settings
        infile = os.path.join(self._conf_dir, which, section + ".yml")
        settings = yaml.load(open(infile))

        # get global / shared settings
        if section == 'main':
            cfg = settings
        else:
            cfg = settings['shared']

        # if a specific type or subsection is specified, include relevant settings
        if target is not None and target in settings:
            cfg.update(settings[target])

        return cfg

    def _get_default_feature_config(self):
        """Returns a dictionary of the default arguments associated with a feature dataset config
           entry"""
        infile = os.path.join(self._conf_dir, 'defaults', 'feature.yml')
        return yaml.load(open(infile))

    def _get_default_pipeline_action_config(self):
        """Returns a dictionary of the default arguments associated with each supported
        transformation"""
        infile = os.path.join(self._conf_dir, 'defaults', 'pipeline.yml')
        return yaml.load(open(infile))

    def _get_default_response_config(self):
        """Returns a dictionary of the default arguments associated with a response dataset config
           entry"""
        infile = os.path.join(self._conf_dir, 'defaults', 'response.yml')
        return yaml.load(open(infile))

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
        self.main_config = self._get_settings()

        # load main snakes configuration file
        with open(config_file) as fp:
            self.main_config.update(yaml.load(fp))

        # Update default arguments with user-specified settings
        self.main_config.update(cmdline_args)

        # Update with arguments specified to SnakefileRenderer constructor
        self.main_config.update(kwargs)

        # Store filepath of config file used
        self.main_config['config_file'] = os.path.abspath(config_file)

        # Update logging level if 'verbose' option is enabled
        if self.main_config['verbose']:
            logging.getLogger().setLevel(logging.DEBUG)

        # check to make sure require dataset elements have been specified
        self._validate_main_config()

        # parse main pipeline section of config
        self.main_config['pipeline'] = self._parse_pipeline_config(
            self.main_config['pipeline'])

        # load feature dataset configs
        for yml in self.main_config['features']:
            self._load_feature_config(yml)

        # load response dataset config
        for yml in self.main_config['response']:
            self._load_response_config(yml)

        # validate feature/response dataset configs
        self._validate_dataset_configs()

    def _load_feature_config(self, input_yaml):
        """Loads a feature / response dataset config file and overides any global settings with
        dataset-specific ones."""
        # load user config
        user_cfg = yaml.load(open(input_yaml))

        # load default feature options
        cfg = self._get_settings('defaults', 'feature', user_cfg['type'])

        # check for unexpected settings
        self._detect_unknown_settings(cfg, user_cfg, input_yaml)

        # load dataset-specific configuration
        cfg.update(user_cfg)

        # if no name specified, default to dataset type (e.g. 'rnaseq')
        if not cfg['name']:
            cfg['name'] = cfg['type']

        # parse filter and transform sections of configs and set appropriate defaults
        cfg['pipeline'] = self._parse_pipeline_config(cfg['pipeline'])

        # in addition to feature-specific settings, any transforms, etc. specified
        # in the main config file are also applied
        for param in ['pipeline', 'clustering', 'gene_sets']:
            if param in self.main_config:
                cfg[param] = cfg[param] + self.main_config[param].copy()

        # store filepath of config file used
        cfg['config_file'] = os.path.abspath(input_yaml)

        self.feature_configs[cfg['name']] = cfg

        logging.debug("Loaded feature config '%s':", cfg['name'])
        logging.debug(pprint.pformat(cfg))

    def _load_response_config(self, input_yaml):
        """Loads a response dataset config file and overides any global settings with
        dataset-specific ones."""
        # load user config
        user_cfg = yaml.load(open(input_yaml))

        # load default response options
        cfg = self._get_settings('defaults', 'response', user_cfg['type'])

        # check for unexpected settings
        self._detect_unknown_settings(cfg, user_cfg, input_yaml)

        # load dataset-specific configuration
        cfg.update(user_cfg)

        # if no name specified, default to dataset type (e.g. 'rnaseq')
        if not cfg['name']:
            cfg['name'] = cfg['type']

        # parse pipeline section of configs and set appropriate defaults
        cfg['pipeline'] = self._parse_pipeline_config(cfg['pipeline'])

        # store filepath of config file used
        cfg['config_file'] = os.path.abspath(input_yaml)

        self.response_config = cfg

        logging.debug("Loaded response config '%s':", cfg['name'])
        logging.debug(pprint.pformat(cfg))

    def _detect_unknown_settings(self, cfg, user_cfg, input_yaml):
        """Checks to see if use configuration contains any unrecognized parameters, and if so,
        raises and exception."""
        unknown_opts = [x for x in user_cfg.keys() if x not in cfg.keys()]

        if unknown_opts:
            msg = "Unexpected configuration options encountered in {}: {}"
            raise Exception(msg.format(os.path.basename(input_yaml), ", ".join(unknown_opts)))

    def _parse_pipeline_config(self, pipeline):
        """
        Loads pipeline section of global or dataset-specific config.

        Pipeline actions (data transformations, etc.) can be specified as a list in one or more of
        the snakes config files. Each entry in the list must be either a single string, indicating
        the type of transformation to be applied (e.g. 'log2'), or a dictionary including the type
        of transformation along with any relevants parameters.
        """
        # if pipeline specified using a list, convert to dict
        # if isinstance(pipeline, list):
        #     pipeline = {pipeline: {'name': action} for action in pipeline}

        # load pipeline entry default settings
        default_params = self._get_default_pipeline_action_config()

        # list to keep track of names used; if multiple versions of the same pipeline are applied,
        # a number will be added to the end of the name to avoid rule collisions
        used_names = []

        # iterate over pipeline steps
        for i, action in enumerate(pipeline):
            # if action is specified as a simple string, convert to a dict with default settings
            if isinstance(action, str):
                action = {'type': action}

            # start with action default options
            cfg = default_params['shared'].copy()

            if action['type'] in default_params:
                cfg.update(default_params[action['type']])

            # overide with user-specified values
            cfg.update(action)

            # if no specific name has been given to the action entry, default to the name of
            # the action itself
            if not cfg['name']:
                cfg['name'] = cfg['type']

            # add a number to non-unique action names
            if cfg['name'] in used_names:
                # number of times action has been used so far
                times_used = len([x for x in used_names if x.startswith(cfg['name'])]) + 1

                cfg['name'] = cfg['name'] + "_" + str(times_used)

            # update used name list
            used_names.append(cfg['name'])

            # store updated action settings
            pipeline[i] = cfg

        return pipeline

    def _validate_main_config(self):
        """Performs some basic check on config dict to make sure required settings are present."""
        #  check for required top-level parameters in main config
        reqs = self._get_settings('required')

        for param in reqs:
            if param not in self.main_config or not self.main_config[param]:
                msg = "Missing required configuration parameter in {}: '{}'"
                config_file = os.path.basename(self.main_config['config_file'])
                raise Exception(msg.format(config_file, param))

    def _validate_dataset_configs(self):
        """Validate dataset-specific configurations"""
        # validate feature configs
        for feature_cfg in self.feature_configs.values():
            # check main dataset configuration options
            reqs = self._get_settings('required', 'feature', feature_cfg['type'])

            # check for required parameters
            for param in reqs:
                if param not in feature_cfg or not feature_cfg[param]:
                    msg = "Missing required configuration parameter in {}: '{}'"
                    raise Exception(msg.format(os.path.basename(feature_cfg['config_file']), param))

            # check feature config sub-sections
            for config_section in ['pipeline', 'gene_sets', 'clustering']:
                self._validate_config_section(feature_cfg[config_section], config_section)

        # validate response config
        # check main dataset configuration options
        reqs = self._get_settings('required', 'response', self.response_config['type'])

        # check for required parameters
        for param in reqs:
            if param not in self.response_config or not self.response_config[param]:
                msg = "Missing required configuration parameter in {}: '{}'"
                config_filename = os.path.basename(self.response_config['config_file'])
                raise Exception(msg.format(config_filename, param))

        # check response pipeline section
        self._validate_config_section(self.response_config['pipeline'], 'pipeline')

    def _validate_config_section(self, config_section, config_section_type):
        """
        Checks for existence of necessary template and required config parameters for a dataset
        config file subsection.

        Arguments
        ---------
        config_section: list
            List of dicts representing a single section in a config file
        config_section_type: str
            Type of config section being processed (e.g. 'feature' or 'pipeline')
        """
        # base template directory
        template_dir = os.path.join(self._template_dir, config_section_type)

        # iterate over subsection entries and validate
        for entry in config_section:
            # check to make sure template exists
            if config_section_type == 'clustering':
                # clustering methods currently all use the same template
                template_filename = 'clustering.snakefile'
            else:
                # gene set, etc. section each have their own separate templates
                template_filename = entry['type'] + '.snakefile'

            if template_filename not in os.listdir(template_dir):
                msg = "Invalid coniguration! Unknown {} entry: '{}'".format(config_section_type,
                                                                            entry['type'])
                raise Exception(msg)

            # check main dataset configuration options
            reqs = self._get_settings('required', config_section_type, entry['type'])

            # check for required parameters
            for param in reqs:
                if param not in entry or not entry[param]:
                    msg = "Missing required {} {} parameter '{}'"
                    raise Exception(msg.format(config_section_type, entry['type'], param))

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
                   PackageLoader('snakes', 'templates/clustering'),
                   PackageLoader('snakes', 'templates/data'),
                   PackageLoader('snakes', 'templates/gene_sets'),
                   PackageLoader('snakes', 'templates/pipeline'),
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
            try:
                return re.sub(r"[^\w]", "_", rule)
            except:
                import pdb; pdb.set_trace()

        env.filters['basename']         = os.path.basename
        env.filters['basename_no_ext']  = basename_no_ext
        env.filters['replace_filename'] = replace_filename
        env.filters['to_rule_name']     = to_rule_name

        # get snakefile jinja2 template
        template = env.get_template('Snakefile')

        # root snakes script directory
        script_dir = os.path.abspath(resource_filename(__name__, 'src'))

        # render template
        snakefile = template.render(config=self.main_config,
                                    features=self.feature_configs,
                                    response=self.response_config,
                                    date_str=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    script_dir=script_dir)

        # save rendered snakefile to disk
        logging.info("Saving Snakefile to %s", self.output_file)

        with open(self.output_file, 'w') as file_handle:
            file_handle.write(snakefile)
