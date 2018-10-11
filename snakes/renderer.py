"""
snakes template renderer
"""
import yaml
from argparse import ArgumentParser
from jinja2 import Environment, PackageLoader
from pkg_resources import resource_filename, Requirement

class SnakefileRenderer(object):
    """Base notebook Renderer class"""
    def __init__(self):
        self.feature_configs = {}
        self.response_configs = {}

        self._load_config()

    def _load_config(self):
        """Parses command-line arguments and loads snakes configuration."""
        # Load configuration
        print("- Loading configuration")

        parser = self._get_args()

        # get input arguments and convert to a dict
        args = parser.parse_args()
        args = dict((k, v) for k, v in list(vars(args).items()) if v is not None)

        # load main snakes configuration file
        config = yaml.load(open('config.yml'))

        # load feature-specific config files
        for feature_yaml in config['features']:
            cfg = yaml.load(open(feature_yaml))
            self.feature_configs[cfg['name']] = cfg

        # load response-specific config files
        for response_yaml in config['response']:
            cfg = yaml.load(open(response_yaml))
            self.response_configs[cfg['name']] = cfg

    def _buid_template(self):
        """Dynamically constructs a jinja2 master Snakefile template"""
        pass

    def _get_args(self):
        """Parses input and returns arguments"""
        parser = ArgumentParser(description='Dynamically generates Snakefiles for data integration and machine learning pipelines.')

        parser.add_argument('-c', '--config',
                            help=('Configuration filepath. (Will look for file named config.yml ' 
                                 'in current working directory, if none specified.)'))

        return parser

    def render(self):
        """Renders snakefile"""
        # env = Environment(loader=PackageLoader('snakes', 'templates'))
        # template = env.get_template(template_name)
        print("- Generating Snakefile...")

        # snakefile = template.render(...)

        # Output snakefile
        # print("- Saving Snakefile to %s" % self.output_file)
        
        # with open(self.output_file, 'w') as fp:
        #     fp.write(html)


