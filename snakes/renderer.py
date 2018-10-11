"""
snakes template renderer
"""
import yaml
from argparse import ArgumentParser
from jinja2 import Environment, ChoiceLoader, PackageLoader
from pkg_resources import resource_filename, Requirement

class SnakefileRenderer(object):
    """Base notebook Renderer class"""
    def __init__(self, config_filepath=None, **kwargs):
        self.config = None

        self.feature_configs = {}
        self.response_configs = {}

        self.output_file = 'Snakefile'

        self._load_config(config_filepath, **kwargs)

    def _load_config(self, config_filepath, **kwargs):
        """Parses command-line arguments and loads snakes configuration."""
        # Load configuration
        print("- Loading configuration")

        parser = self._get_args()

        # get input arguments and convert to a dict
        args = parser.parse_args()
        args = dict((k, v) for k, v in list(vars(args).items()) if v is not None)

        # Check for configuration file specified in the SnakefileRenderer constructor.
        if config_filepath is not None:
            config_file = config_filepath
            if not os.path.isfile(config_file):
                print("Invalid configuration path specified: %s" % args['config'])
                sys.exit()

        # load main snakes configuration file
        self.config = yaml.load(open('config.yml'))

        # Update default arguments with user-specified settings
        self.config.update(args)

        # Update with arguments specified to Notebook constructor
        self.config.update(kwargs)

        # load feature-specific config files
        for feature_yaml in self.config['features']:
            cfg = yaml.load(open(feature_yaml))
            self.feature_configs[cfg['name']] = cfg

        # load response-specific config files
        for response_yaml in self.config['response']:
            cfg = yaml.load(open(response_yaml))
            self.response_configs[cfg['name']] = cfg

    def _get_args(self):
        """Parses input and returns arguments"""
        parser = ArgumentParser(description='Dynamically generates Snakefiles for data integration and machine learning pipelines.')

        parser.add_argument('-c', '--config',
                            help=('Configuration filepath. (Will look for file named config.yml ' 
                                 'in current working directory, if none specified.)'))

        return parser

    def render(self):
        """Renders snakefile"""
        print("- Generating Snakefile...")

        # get snakefile jinja2 template
        loaders = [PackageLoader('snakes', 'templates'), 
                   PackageLoader('snakes', 'templates/data')]
        env = Environment(loader=ChoiceLoader(loaders))
        template = env.get_template('Snakefile')

        # render template
        snakefile = template.render(config=self.config, features=self.feature_configs,
                                    responses=self.response_configs)

        # save rendered snakefile to disk
        print("- Saving Snakefile to {}".format(self.output_file))
        
        with open(self.output_file, 'w') as fp:
            fp.write(snakefile)


