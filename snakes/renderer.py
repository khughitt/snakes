"""
snakes template renderer
"""
import datetime
import logging
import pprint
import os
import re
import pathlib
import sys
import yaml
from argparse import ArgumentParser
from jinja2 import Environment, ChoiceLoader, PackageLoader
from pkg_resources import resource_filename
from snakes.util import recursive_update

class SnakefileRenderer():
    """Base SnakefileRenderer class"""
    def __init__(self, config_filepath=None, **kwargs):
        self.config = None
        self.output_file = 'Snakefile'

        # dict to keep track of names used; if multiple versions of the same rule are 
        # applied, a number will be added to the end of the name to avoid rule collisions
        self._rule_names = {}

        self._setup_logger()

        self._conf_dir = os.path.abspath(resource_filename(__name__, 'conf'))
        self._template_dir = os.path.abspath(resource_filename(__name__, 'templates'))

        # load required and default settings
        with open(os.path.join(self._conf_dir, "required.yml")) as fp:
            self._required_params = yaml.load(fp)
        with open(os.path.join(self._conf_dir, "defaults.yml")) as fp:
            self._default_params = yaml.load(fp)

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

    def _load_config(self, config_filepath, **kwargs):
        """Parses command-line arguments and loads snakes configuration."""
        # get command-line arguments and convert to a dict
        parser = self._get_args()
        cmdline_args = parser.parse_args()
        cmdline_args = dict((k, v) for k, v in list(vars(cmdline_args).items()) if v is not None)

        # if user specified a config filepath on the command-line, use that path
        if 'config' in cmdline_args:
            config_file = cmdline_args['config']
        elif config_filepath is not None:
            # otherwise use filepath specified in constructor, if specified
            config_file = config_filepath
        else:
            # finally, check for config file in current working directory
            config_file = 'config.yml'

        # check to make sure config filepath is valid
        if not os.path.isfile(config_file):
            logging.error("Config error: invalid configuration path specified: %s", config_file)
            sys.exit()

        logging.info("Using configuration: %s", config_file)

        # get default main configuration options
        self.config = self._default_params['shared']['main'].copy()

        # load user-provided main snakes config file
        with open(config_file) as fp:
            # self.config.update(yaml.load(fp))
            self.config = recursive_update(self.config, yaml.load(fp))

        # overide any settings specified via the command-line
        self.config.update(cmdline_args)

        # overide any settings specified via the SnakefileRenderer constructor
        self.config.update(kwargs)

        # Store filepath of config file used
        self.config['config_file'] = os.path.abspath(config_file)

        # update logging level if 'verbose' option is enabled
        if self.config['verbose']:
            logging.getLogger().setLevel(logging.DEBUG)

        # check to make sure required config elements have been specified
        self._validate_main_config()

        # load dataset-specific configurations; each should be specified either as a filepath to a
        # dataset-specific yaml file, or as a dict instance
        data_sources = {}

        for data_source in self.config['data_sources']:
            # separate file
            if type(data_source) == str:
                cfg = yaml.load(open(data_source))
                cfg['config_file'] = os.path.abspath(data_source)
            elif type(data_source) == dict:
                # inline config section
                cfg = data_source

            # validate and parse datasource config section
            cfg = self._parse_data_source_config(cfg)

            # add to dict of datasource-specific configs
            data_sources[cfg['name']] = cfg
        
        self.config['data_sources'] = data_sources

    def _parse_data_source_config(self, user_cfg):
        """Loads a dataset config file and overides any global settings with
        dataset-specific ones."""

        # load default dataset config options
        cfg = self._default_params['shared']['data_source'].copy()

        # add datatype-specific requirements, if they exist
        if 'data_type' in user_cfg and user_cfg['data_type'] in self._default_params['custom']['data_source']:
            cfg.update(self._default_params['custom']['data_source'][user_cfg['data_type']])

        logging.info("Parsing %s config", user_cfg['name'])

        # check for any unsupported settings
        self._detect_unknown_settings(cfg, user_cfg)

        # overide default settings with user-provided ones
        # cfg.update(user_cfg)
        cfg = recursive_update(cfg, user_cfg)

        # get file extension (excluding .gz suffix, if present)
        ext = pathlib.Path(cfg['path'].lower().replace('.gz', '')).suffix

        # determine input file format / separator, if not specified
        if cfg['format'] == '':
            # csv
            if ext == '.csv':
                cfg['format'] = 'csv'
                cfg['sep'] = ','
            elif ext in ['.tsv', '.tab', '.txt']:
                # tab-delimited
                cfg['format'] = 'tsv'
                cfg['sep'] = '\t'
            elif ext in ['.xls', '.xlsx']:
                # excel spreadsheet
                cfg['format'] = 'xls'

        if cfg['format'] in ['csv', 'tsv'] and cfg['sep'] == '':
            # csv
            if ext == '.csv':
                cfg['sep'] = ','
            elif ext in ['.tsv', '.tab', '.txt']:
                # tab-delimited
                cfg['sep'] = '\t'

        # parse pipeline section config section
        cfg['pipeline'] = self._parse_pipeline_config(cfg['pipeline'], cfg['name'])

        # validate data source config
        self._validate_data_source_config(cfg)

        # store parsed data source config
        return cfg

    def _detect_unknown_settings(self, supported_cfg, user_cfg):
        """
        Checks to see if use configuration contains any unrecognized parameters, and if so,
        raises and exception.
       
        Parameters:
        -----------
        supported_cfg: dict
            Dictionary representation of configuration section including all supported parameters.
        user_cfg: dict
            Dictionary representation of corresponding user-provided configuration section 
        """
        unknown_opts = [x for x in user_cfg.keys() if x not in supported_cfg.keys()]

        if unknown_opts:
            msg = "Config error: unexpected configuration options encountered for {}: {}"
            sys.exit(msg.format(user_cfg['name'], ", ".join(unknown_opts)))

    def _parse_pipeline_config(self, pipeline_cfg, data_source_name):
        """
        Loads pipeline config section

        Pipeline actions (data transformations, etc.) can be specified as a list in one or more of
        the snakes config files. Each entry in the list must be either a single string, indicating
        the type of action to be applied (e.g. 'log2'), or a dictionary including the type of
        action along with any relevants parameters.
        """
        # iterate over pipeline actions and recursively parse
        for i, pipeline_action_cfg in enumerate(pipeline_cfg):        
            pipeline_cfg[i] = self._parse_pipeline_action_config(pipeline_action_cfg,
                                                                 data_source_name)

        return pipeline_cfg

    def _parse_pipeline_action_config(self, pipeline_action_cfg, data_source_name):
        """Parses a single action in a snakes pipeline config section"""
        # if no parameters specified, add placeholder empty dict
        if isinstance(pipeline_action_cfg, str):
            pipeline_action_cfg = {pipeline_action_cfg: {}}

        # split into action name and parameters
        action, action_params = list(pipeline_action_cfg.items())[0]

        # if a "branch" action is encountered, parse sub-config(s)
        if action == 'branch':
            # parse any sub-pipelines defined
            return self._parse_pipeline_config(action_params, data_source_name)

        # check to make sure parameters specified as a dict (in case user accidentally uses
        # a list in the yaml)
        if type(action_params) != dict:
            msg = "Config error: parameters for {} must be specified as a YAML dictionary."
            sys.exit(msg.format(action))

        # get pipeline action default params (for now, just 'rule_name' and 'action')
        cfg = self._default_params['shared']['pipeline'].copy()

        if action in self._default_params['custom']['pipeline']:
            cfg.update(self._default_params['custom']['pipeline'][action])

        # overide with any user-specified config values
        cfg.update(action_params)

        # store pipeline action name with params
        cfg['action'] = action

        # if no specific rule name has been given to the pipeline entry, use:
        # <data_source>_<action>
        if not cfg['rule_name']:
            cfg['rule_name'] = "%s_%s" % (data_source_name, action)

        # only allow letters, number, and underscores in rule names
        cfg['rule_name'] = re.sub(r"[^\w]", "_", cfg['rule_name'])

        # check to see if rule name has already been used
        if cfg['rule_name'] in self._rule_names:
            # if name has already been used, increment counter and add to config
            self._rule_names[cfg['rule_name']] += 1
            cfg['rule_name'] += "_%d" % self._rule_names[cfg['rule_name']]
        else:
            # if this is the first time the name has been encountered, add to counter
            self._rule_names[cfg['rule_name']] = 1

        return cfg

    def _validate_main_config(self):
        """Performs some basic check on config dict to make sure required settings are present."""
        #  check for required top-level parameters in main config
        for param in self._required_params['shared']['main']:
            if param not in self.config or not self.config[param]:
                msg = "Config error: missing required configuration parameter in {}: '{}'"
                config_file = os.path.basename(self.config['config_file'])
                sys.exit(msg.format(config_file, param))

    def _validate_data_source_config(self, data_source_cfg):
        """Validate dataset-specific configurations"""
        # get shared dataset required params
        reqs = self._required_params['shared']['data_source'].copy()

        # add datatype-specific requirements, if they exist
        if data_source_cfg['data_type'] in self._required_params['custom']['data_source']:
            reqs.update(self._required_params['custom']['data_source'][data_source_cfg['data_type']])

        # check for required parameters
        for param in reqs:
            if param not in data_source_cfg or not data_source_cfg[param]:
                msg = "Config error: missing required configuration parameter in {}: '{}'"
                sys.exit(msg.format(os.path.basename(data_source_cfg['config_file']), param))

        # check pipeline sub-section of data source config
        self._validate_config_section(data_source_cfg['pipeline'], 'pipeline')

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
            # recurse on pipeline branches
            if type(entry) == list:
                self._validate_config_section(entry, 'pipeline')
                continue

            # TODO 2019-01-20 clean-up handling of 'type' / 'action' in data_source and pipeline
            # config sections...
            if config_section_type == 'pipeline':
                template_filename = entry['action'] + '.snakefile'

            if template_filename not in os.listdir(template_dir):
                msg = "Config error: invalid coniguration! Unknown {} entry: '{}'".format(config_section_type,
                                                                            entry['action'])
                sys.exit(msg)

            # check main dataset configuration options
            reqs = self._required_params['shared'][config_section_type].copy()

            # add entry-specific requirements, if they exist
            if entry['action'] in self._required_params['custom'][config_section_type]:
                reqs.update(self._required_params['custom'][config_section_type][entry['action']])

            # check for required parameters
            for param in reqs:
                if param not in entry or not entry[param]:
                    msg = "Config error: Missing required {} {} parameter '{}'"
                    sys.exit(msg.format(config_section_type, entry['action'], param))

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
                   PackageLoader('snakes', 'templates/annotations'),
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
        def basename_and_parent_dir(filepath):
            """Strips directories and extension from a filepath"""
            path, filename = os.path.split(filepath)
            return os.path.join(os.path.basename(path), filename)

        def basename_no_ext(filepath):
            """Strips directories and extension from a filepath"""
            return os.path.basename(os.path.splitext(filepath)[0]) 

        def is_list(value):
            """Checks if variable is of type list"""
            return isinstance(value, list)

        def replace_filename(filepath, filename):
            """Repaces the filename portion of a filepath"""
            return os.path.join(os.path.dirname(filepath), filename)

        def to_rule_name(rule):
            """Takes a string and replaces characters that aren't allowed in snakemake rule names
            with underscores"""
            try:
                return re.sub(r"[^\w]", "_", rule)
            except:
                print("to_rule_name() failed!")
                import pdb; pdb.set_trace()

        env.filters['basename'] = os.path.basename
        env.filters['basename_and_parent_dir'] = basename_and_parent_dir
        env.filters['basename_no_ext'] = basename_no_ext
        env.filters['expanduser'] = os.path.expanduser
        env.filters['is_list'] = is_list
        env.filters['replace_filename'] = replace_filename
        env.filters['to_rule_name'] = to_rule_name

        # get snakefile jinja2 template
        template = env.get_template('Snakefile')

        # root snakes script directory
        script_dir = os.path.abspath(resource_filename(__name__, 'src'))

        # render template
        snakefile = template.render(config=self.config,
                                    date_str=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    script_dir=script_dir)

        # save rendered snakefile to disk
        logging.info("Saving Snakefile to %s", self.output_file)

        with open(self.output_file, 'w') as file_handle:
            file_handle.write(snakefile)
