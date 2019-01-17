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
        self.data_configs = {}

        self.output_file = 'Snakefile'

        self._setup_logger()

        self._conf_dir = os.path.abspath(resource_filename(__name__, 'conf'))
        self._template_dir = os.path.abspath(resource_filename(__name__, 'templates'))

        self._required_params = yaml.load(os.path.join(self._conf_dir, "required.yml"))
        self._default_params = yaml.load(os.path.join(self._conf_dir, "defaults.yml"))

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

    def _get_default_data_config(self):
        """Returns a dictionary of the default arguments associated with a dataset config
           entry"""
        infile = os.path.join(self._conf_dir, 'defaults', 'data_source.yml')
        return yaml.load(open(infile))

    def _get_pipeline_defaults(self):
        """Returns a dictionary of the default arguments associated with each supported
        transformation"""
        infile = os.path.join(self._conf_dir, 'defaults', 'pipeline.yml')
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

        # get default main configuration options
        self.main_config = self._default_params['shared']['main'].copy()

        # load user-provided main snakes config file
        with open(config_file) as fp:
            self.main_config.update(yaml.load(fp))

        # overide any settings specified via the command-line
        self.main_config.update(cmdline_args)

        # overide any settings specified via the SnakefileRenderer constructor
        self.main_config.update(kwargs)

        # Store filepath of config file used
        self.main_config['config_file'] = os.path.abspath(config_file)

        # Update logging level if 'verbose' option is enabled
        if self.main_config['verbose']:
            logging.getLogger().setLevel(logging.DEBUG)

        # check to make sure required config elements have been specified
        self._validate_main_config()

        # load dataset-specific config files
        for yml in self.main_config['data_sources']:
            self._load_data_config(yml)

        # validate dataset configs
        self._validate_data_configs()

    def _load_data_config(self, input_yaml):
        """Loads a dataset config file and overides any global settings with
        dataset-specific ones."""
        # load user-provided dataset config file
        user_cfg = yaml.load(open(input_yaml))

        # load default dataset config options
        cfg = self._default_params['shared']['data_source'].copy()

        # check for any unsupported settings
        self._detect_unknown_settings(cfg, user_cfg, input_yaml)

        # overide default settings with user-provided ones
        cfg.update(user_cfg)

        # if no name specified, default to dataset type (e.g. 'rnaseq')
        if not cfg['name']:
            cfg['name'] = cfg['type']

        # parse pipeline section config section
        cfg['pipeline'] = self._parse_pipeline_config(cfg['pipeline'])

        # store filepath of config file used
        cfg['config_file'] = os.path.abspath(input_yaml)

        # store parsed data source config
        self.data_configs[cfg['name']] = cfg

        logging.debug("Loaded data config '%s':", cfg['name'])
        logging.debug(pprint.pformat(cfg))

    def _detect_unknown_settings(self, supported_cfg, user_cfg, input_yaml):
        """
        Checks to see if use configuration contains any unrecognized parameters, and if so,
        raises and exception.
       
        Parameters:
        -----------
        supported_cfg: dict
            Dictionary representation of configuration section including all supported parameters.
        user_cfg: dict
            Dictionary representation of corresponding user-provided configuration section 
        input_yaml: str
            Filepath to config file currently being analyzed; Used in error message if an invalid
            option is encountered.
        """
        unknown_opts = [x for x in user_cfg.keys() if x not in supported_cfg.keys()]

        if unknown_opts:
            msg = "Unexpected configuration options encountered in {}: {}"
            raise Exception(msg.format(os.path.basename(input_yaml), ", ".join(unknown_opts)))

    def _parse_pipeline_config(self, pipeline_cfg):
        """
        Loads pipeline config section

        Pipeline steps (data transformations, etc.) can be specified as a list in one or more of
        the snakes config files. Each entry in the list must be either a single string, indicating
        the type of transformation to be applied (e.g. 'log2'), or a dictionary including the type
        of transformation along with any relevants parameters.
        """
        # if pipeline specified using a list, convert to dict
        # if isinstance(pipeline, list):
        #     pipeline = {pipeline: {'name': step} for step in pipeline}

        # dict to keep track of names used; if multiple versions of the same pipeline are applied,
        # a number will be added to the end of the name to avoid rule collisions
        name_counter = {}

        # get pipeline step shared default params
        cfg = self._default_params['shared']['pipeline'].copy()

        # iterate over pipeline steps
        for i, pipeline_step_cfg in enumerate(pipeline_cfg):
            # if step is specified as a simple string, convert to a dict with default settings
            if isinstance(pipeline_step_cfg, str):
                pipeline_step_cfg = {'type': action}

            # TODO: CHECK FOR BRANCHING...
            if pipeline_step_cfg['type'] in self._default_params['custom']['pipeline']:
                cfg.update(self._default_params['custom']['pipeline'][pipeline_step_cfg['type']])

            # overide with any user-specified config values
            cfg.update(pipeline_step_cfg)

            # if no specific name has been given to the pipeline entry, default to the name of
            # the step itself
            if not cfg['name']:
                cfg['name'] = cfg['type']

            # add a number to non-unique step names
            if cfg['name'] in name_counter:
                # if name has already been used, increment counter and add to config
                name_counter[cfg['name']] += 1
                cfg['name'] = cfg['name'] + "_" + str(name_counter[cfg['name']])
            else:
                # otherwise, if this is the first time the name has been encountered, add to counter
                name_counter[cfg['name']] = 1

            # store updated pipeline step parameters
            pipeline_cfg[i] = cfg

        return pipeline_cfg

    def _validate_main_config(self):
        """Performs some basic check on config dict to make sure required settings are present."""
        #  check for required top-level parameters in main config
        for param in self._required_params['shared']['main']:
            if param not in self.main_config or not self.main_config[param]:
                msg = "Missing required configuration parameter in {}: '{}'"
                config_file = os.path.basename(self.main_config['config_file'])
                raise Exception(msg.format(config_file, param))

    def _validate_data_configs(self):
        """Validate dataset-specific configurations"""
        for data_cfg in self.data_configs.values():
            # get shared dataset required params
            reqs = self._required_params['shared']['data_source']:

            # add datatype-specific requirements, if they exist
            if data_cfg['type'] in self._required_params['custom']['data_source']:
                reqs.update(self._required_params['custom']['data_source'][data_cfg['type']])

            # check for required parameters
            for param in reqs:
                if param not in data_cfg or not data_cfg[param]:
                    msg = "Missing required configuration parameter in {}: '{}'"
                    raise Exception(msg.format(os.path.basename(data_cfg['config_file']), param))

            # check pipeline sub-section
            self._validate_config_section(data_cfg['pipeline'], 'pipeline')

    def _validate_config_section(self, config_section, config_section_type):
        """
        Checks for existence of necessary template and required config parameters for a dataset
        config file subsection.

        Arguments
        ---------
        config_section: list
            List of dicts representing a single section in a config file
        config_section_type: str
            Type of config section being processed (e.g. 'data_source' or 'pipeline')
        """
        # base template directory
        template_dir = os.path.join(self._template_dir, config_section_type)

        # iterate over subsection entries and validate
        for entry in config_section:
            # check to make sure template exists
            # if config_section_type == 'clustering':
            #     # clustering methods currently all use the same template
            #     template_filename = 'clustering.snakefile'
            # else:
                # gene set, etc. section each have their own separate templates
                # template_filename = entry['type'] + '.snakefile'
            template_filename = entry['type'] + '.snakefile'

            if template_filename not in os.listdir(template_dir):
                msg = "Invalid coniguration! Unknown {} entry: '{}'".format(config_section_type,
                                                                            entry['type'])
                raise Exception(msg)

            # check main dataset configuration options
            reqs = self._required_params['shared'][config_section_type].copy()

            # add entry-specific requirements, if they exist
            if entry['type'] in self._required_params['custom'][config_section_type]:
                reqs.update(self._required_params['custom'][config_section_type][entry['type']])

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
                                    data_sources=self.data_configs,
                                    date_str=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    script_dir=script_dir)

        # save rendered snakefile to disk
        logging.info("Saving Snakefile to %s", self.output_file)

        with open(self.output_file, 'w') as file_handle:
            file_handle.write(snakefile)
