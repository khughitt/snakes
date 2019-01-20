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
        self.config = None
        self.output_file = 'Snakefile'

        # dict to keep track of names used; if multiple versions of the same pipeline are 
        # applied, a number will be added to the end of the name to avoid rule collisions
        self._rule_name_counter = {}

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

    def _get_default_data_source_config(self):
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
            logging.error("Invalid configuration path specified: %s", config_file)
            sys.exit()

        logging.info("Using configuration: %s", config_file)

        # get default main configuration options
        self.config = self._default_params['shared']['main'].copy()

        # load user-provided main snakes config file
        with open(config_file) as fp:
            self.config.update(yaml.load(fp))

        # overide any settings specified via the command-line
        self.config.update(cmdline_args)

        # overide any settings specified via the SnakefileRenderer constructor
        self.config.update(kwargs)

        # Store filepath of config file used
        self.config['config_file'] = os.path.abspath(config_file)

        # Update logging level if 'verbose' option is enabled
        if self.config['verbose']:
            logging.getLogger().setLevel(logging.DEBUG)

        # check to make sure required config elements have been specified
        self._validate_main_config()

        # load dataset-specific config files and replace original list of filepaths
        data_sources = {}

        for data_source in self.config['data_sources']:
            # sub-config yaml filepath
            if type(data_source) == str:
                cfg = yaml.load(open(data_source))
                cfg['config_file'] = os.path.abspath(data_source)

            else if type(data_source) == dict:
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

        # check for any unsupported settings
        self._detect_unknown_settings(cfg, user_cfg)

        # overide default settings with user-provided ones
        cfg.update(user_cfg)

        # parse pipeline section config section
        cfg['pipeline'] = self._parse_pipeline_config(cfg['pipeline'])

        # validate data source config
        self._validate_data_source_config(cfg)

        logging.debug("Loaded data config '%s':", cfg['name'])
        logging.debug(pprint.pformat(cfg))

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
            msg = "Unexpected configuration options encountered for {}: {}"
            raise Exception(msg.format(cfg['name'], ", ".join(unknown_opts)))

    def _parse_pipeline_config(self, pipeline_cfg):
        """
        Loads pipeline config section

        Pipeline steps (data transformations, etc.) can be specified as a list in one or more of
        the snakes config files. Each entry in the list must be either a single string, indicating
        the type of transformation to be applied (e.g. 'log2'), or a dictionary including the type
        of transformation along with any relevants parameters.
        """
        # iterate over pipeline steps and recursively parse
        for i, pipeline_step_cfg in enumerate(pipeline_cfg):        
            pipeline_cfg[i] = self._parse_pipeline_step_config(pipeline_step_cfg)

        return pipeline_cfg

    def _parse_pipeline_step_config(self, pipeline_step_cfg):
        """Parses a single step in a snakes pipeline config section"""
        # if no parameters specified, add placeholder empty dict
        if isinstance(pipeline_step_cfg, str):
            pipeline_step_cfg = {pipeline_step_cfg: {}}

        # split into step name and parameters
        step_name, step_params = list(pipeline_step_cfg.items())[0]

        # if a "branch" action is encountered, parse sub-config(s)
        if step_name == 'branch':
            # parse any sub-pipelines defined
            return self._parse_pipeline_config(step_params)

        # get pipeline step default params (for now, just 'name' and 'id')
        cfg = self._default_params['shared']['pipeline'].copy()

        if step_name in self._default_params['custom']['pipeline']:
            cfg.update(self._default_params['custom']['pipeline'][step_name])

        # overide with any user-specified config values
        cfg.update(step_params)

        # if no specific name has been given to the pipeline entry, default to the name of
        # the pipeline step itself
        if not cfg['name']:
            cfg['name'] = step_name

        # add a number to non-unique step names
        if cfg['name'] in self._rule_name_counter:
            # if name has already been used, increment counter and add to config
            self._rule_name_counter[cfg['name']] += 1
            cfg['name'] = cfg['name'] + "_" + str(self._rule_name_counter[cfg['name']])
        else:
            # otherwise, if this is the first time the name has been encountered, add to counter
            self._rule_name_counter[cfg['name']] = 1

        return cfg

    def _validate_main_config(self):
        """Performs some basic check on config dict to make sure required settings are present."""
        #  check for required top-level parameters in main config
        for param in self._required_params['shared']['main']:
            if param not in self.config or not self.config[param]:
                msg = "Missing required configuration parameter in {}: '{}'"
                config_file = os.path.basename(self.config['config_file'])
                raise Exception(msg.format(config_file, param))

    def _validate_data_source_config(self, data_source_config):
        """Validate dataset-specific configurations"""
            # get shared dataset required params
            reqs = self._required_params['shared']['data_source']:

            # add datatype-specific requirements, if they exist
            if data_source_cfg['type'] in self._required_params['custom']['data_source']:
                reqs.update(self._required_params['custom']['data_source'][data_source_cfg['type']])

            # check for required parameters
            for param in reqs:
                if param not in data_source_cfg or not data_source_cfg[param]:
                    msg = "Missing required configuration parameter in {}: '{}'"
                    raise Exception(msg.format(os.path.basename(data_source_cfg['config_file']), param))

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
        snakefile = template.render(config=self.config,
                                    date_str=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    script_dir=script_dir)

        # save rendered snakefile to disk
        logging.info("Saving Snakefile to %s", self.output_file)

        with open(self.output_file, 'w') as file_handle:
            file_handle.write(snakefile)
