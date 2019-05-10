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
from snakes.wrangler import SnakeWrangler


class SnakefileRenderer:
    """Base SnakefileRenderer class"""

    def __init__(self, config_filepath=None, **kwargs):
        self.config = None
        self.output_file = "Snakefile"

        self._setup_logger()

        self._conf_dir = os.path.abspath(resource_filename(__name__, "conf"))
        self._template_dir = os.path.abspath(resource_filename(__name__, "templates"))

        # load action required / default parameters
        with open(os.path.join(self._conf_dir, "actions.yml")) as fp:
            self._supported_actions = yaml.load(fp, Loader=yaml.FullLoader)

        self._load_config(config_filepath, **kwargs)

    @staticmethod
    def _setup_logger():
        """Sets up logging environment"""
        root = logging.getLogger()
        root.setLevel(logging.INFO)

        log_handle = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(levelname)s] (%(asctime)s) - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        log_handle.setFormatter(formatter)
        root.addHandler(log_handle)

        logging.info("Initializing snakes")

    def _load_config(self, config_filepath, **kwargs):
        """Parses command-line arguments and loads snakes configuration."""
        # get command-line arguments and convert to a dict
        parser = self._get_args()
        cmdline_args = parser.parse_args()
        cmdline_args = dict(
            (k, v) for k, v in list(vars(cmdline_args).items()) if v is not None
        )

        # if user specified a config filepath on the command-line, use that path
        if "config" in cmdline_args:
            config_file = cmdline_args["config"]
        elif config_filepath is not None:
            # otherwise use filepath specified in constructor, if specified
            config_file = config_filepath
        else:
            # finally, check for config file in current working directory
            config_file = "config.yml"

        # check to make sure config filepath is valid
        if not os.path.isfile(config_file):
            logging.error(
                "Config error: invalid configuration path specified: %s", config_file
            )
            sys.exit()

        logging.info("Using configuration: %s", config_file)

        # get default main configuration options
        with open(os.path.join(self._conf_dir, "defaults.yml")) as fp:
            self.config = yaml.load(fp, Loader=yaml.FullLoader)

        # load user-provided main snakes config file
        with open(config_file) as fp:
            # self.config.update(yaml.load(fp, Loader=yaml.FullLoader))
            self.config = recursive_update(
                self.config, yaml.load(fp, Loader=yaml.FullLoader)
            )

        # overide any settings specified via the command-line
        self.config.update(cmdline_args)

        # overide any settings specified via the SnakefileRenderer constructor
        self.config.update(kwargs)

        # Store filepath of config file used
        self.config["config_file"] = os.path.abspath(config_file)

        # update logging level if 'verbose' option is enabled
        if self.config["verbose"]:
            logging.getLogger().setLevel(logging.DEBUG)

        # check to make sure required config elements have been specified
        self._validate_main_config()

        # create a new SnakeWrangler instance to manage rules
        output_dir = "/".join(
            [os.path.expanduser(self.config["output_dir"]), self.config["version"]]
        )
        self._wrangler = SnakeWrangler(output_dir)

        # load dataset-specific configurations; each should be specified either as a filepath to a
        # dataset-specific yaml file, or as a dict instance
        datasets = {}

        for dataset in self.config["datasets"]:
            # separate file
            if type(dataset) == str:
                cfg = yaml.load(open(dataset), Loader=yaml.FullLoader)
                cfg["config_file"] = os.path.abspath(dataset)
            elif type(dataset) == dict:
                # inline config section
                cfg = dataset

            # validate and parse datasource config section
            cfg = self._parse_dataset_config(cfg)

            # add to dict of datasource-specific configs
            datasets[cfg["name"]] = cfg

        self.config["datasets"] = datasets

    def _parse_dataset_config(self, user_cfg):
        """Loads a dataset config file and overides any global settings with any dataset-specific ones."""

        # default dataset parameters
        dataset = {
            "file_type": "",
            "encoding": "utf-8",
            "path": "",
            "name": "",
            "xid": "x",
            "yid": "y",
            "sep": "",
            "sheet": 0,
            "config_file": "",
            "index_col": 0,
            "actions": [],
        }

        logging.info("Parsing %s config", user_cfg["name"])

        # check for any unsupported settings
        self._detect_unknown_settings(dataset, user_cfg)

        # overide default settings with user-provided ones
        # dataset.update(user_cfg)
        dataset = recursive_update(dataset, user_cfg)

        # get file extension (excluding .gz suffix, if present)
        ext = pathlib.Path(dataset["path"].lower().replace(".gz", "")).suffix

        # if data source not specified, attempt to guess from file extension
        if dataset["file_type"] == "":
            if ext in [".csv", ".tsv", ".tab"]:
                # comma-separated / tab-delmited
                dataset["file_type"] = "csv"
            elif ext in [".xls", ".xlsx"]:
                # excel spreadsheet
                dataset["file_type"] = "xls"
            else:
                msg = "Config error: could not determine appropriate file_type for {}"
                sys.exit(msg.format(dataset["path"]))

        # determine delimiter for csv/tsv files
        if dataset["file_type"] == "csv" and dataset["sep"] == "":
            if ext in [".csv"]:
                dataset["sep"] = ","
            elif ext in [".tsv", ".tab"]:
                dataset["sep"] = "\t"

        # if a str index column value is specified, wrap in quotation marks so that it is handled
        # properly in templates
        if isinstance(dataset["index_col"], str):
            dataset["index_col"] = "'{}'".format(dataset["index_col"])

        # parse actions section config section
        dataset["actions"] = self._parse_actions_list(
            dataset["actions"], dataset["name"]
        )

        # validate dataset config
        self._validate_dataset_config(dataset)

        # separate actions from rest of dataset parameters
        dataset_actions = dataset["actions"]

        del dataset["actions"]

        # add actions to SnakeWrangler instance
        self._wrangler.add(dataset["name"], dataset_actions, **dataset)

        # store parsed dataset config
        return dataset

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
            msg = (
                "Config error: unexpected configuration options encountered for {}: {}"
            )
            sys.exit(msg.format(user_cfg["name"], ", ".join(unknown_opts)))

    def _parse_actions_list(self, actions_cfg, dataset_name):
        """
        Loads actions config section

        The "actions_cfg" parameter should be a list of strings (action name with no
        parametes), and dicts (i.e. "{'action_name': { params }}").

        A special case is "branch" actions which themselves contain a nested list of
        actions, e.g.:

        [
            "action1",
            { "action2": { "param1": "foo" } },
            { "branch": [{ "action3": { "param2": "bar" } }]
        ]
        """
        # iterate over actions and parse
        for i, cfg in enumerate(actions_cfg):
            actions_cfg[i] = self._parse_action(cfg, dataset_name)

        return actions_cfg

    def _parse_action(self, action_cfg, dataset_name):
        """Parses a single action config section"""
        # if no parameters specified, add placeholder empty dict
        if isinstance(action_cfg, str):
            action_cfg = {action_cfg: {}}

        # split into action name and parameters
        action_name, action_params = list(action_cfg.items())[0]

        # group meta-action
        if action_name == "group":
            action_params["action_name"] = "group"
            action_params["actions"] = self._parse_actions_list(
                action_params["actions"], dataset_name
            )
        # branch meta-action
        elif action_name == "branch":
            return self._parse_actions_list(action_params, dataset_name)

        # check to make sure parameters specified as a dict (in case user accidentally uses
        # a list in the yaml)
        if type(action_params) != dict:
            msg = "Config error: parameters for {} must be specified as a YAML dictionary."
            sys.exit(msg.format(action_name))

        # get default action params
        cfg = {
            "action_name": action_name,
            "filename": "",
            "groupable": True,
            "local": False,
        }

        if action_name in self._supported_actions:
            cfg.update(self._supported_actions[action_name]["defaults"])

        # overide with any user-specified config values
        cfg.update(action_params)

        return cfg

    def _validate_main_config(self):
        """Performs some basic check on config dict to make sure required settings are present."""
        #  check for required top-level parameters in main config
        required_params = {"name": str, "version": str, "datasets": list}
        for param, expected_type in required_params.items():
            if param not in self.config or not self.config[param]:
                msg = (
                    "Config error: missing required configuration parameter in {}: '{}'"
                )
                config_file = os.path.basename(self.config["config_file"])
                sys.exit(msg.format(config_file, param))
            elif not isinstance(self.config[param], expected_type):
                msg = "Config error: parameter is of unexpected type {}: '{}' (expected: '{}')"
                config_file = os.path.basename(self.config["config_file"])
                sys.exit(msg.format(config_file, param, expected_type))

    def _validate_dataset_config(self, dataset_cfg):
        """Validate dataset-specific configurations"""
        # required dataset parameters
        required_params = {"name": str, "path": str}

        # check for required parameters
        for param, expected_type in required_params.items():
            if param not in dataset_cfg or not dataset_cfg[param]:
                msg = (
                    "Config error: missing required configuration parameter in {}: '{}'"
                )
                config_file = os.path.basename(dataset_cfg["config_file"])
                sys.exit(msg.format(config_file, param))
            elif not isinstance(dataset_cfg[param], expected_type):
                msg = "Config error: parameter is of unexpected type {}: '{}' (expected: '{}')"
                config_file = os.path.basename(dataset_cfg["config_file"])
                sys.exit(msg.format(config_file, param, expected_type))

        # check action sub-section of dataset config
        self._validate_actions_config(
            dataset_cfg["actions"], os.path.basename(dataset_cfg["config_file"])
        )

    def _validate_actions_config(self, actions_config, config_file):
        """
        Checks for existence of necessary template and required config parameters for a dataset
        config file subsection.

        Arguments
        ---------
        actions_config: list
            List of dicts representing a single section in a config file
        config_file: str
            Filename of configuration file being processed
        """
        # base template directory
        base_dir = os.path.join(self._template_dir, "actions")

        # iterate over subsection entries and validate
        for entry in actions_config:
            # recurse on actions branches
            if type(entry) == list:
                # branch
                self._validate_actions_config(entry, config_file)
                continue
            elif entry["action_name"] == "group":
                # group
                self._validate_actions_config(entry["actions"], config_file)
                continue

            # get expected path to template
            template_dir = os.path.join(base_dir, entry["action_name"].split("_")[0])
            template_filename = entry["action_name"] + ".snakefile"

            # check for valid action
            if template_filename not in os.listdir(template_dir):
                msg = "[ERROR] Unknown action entry '{}'".format(entry["action_name"])
                sys.exit(msg)

            # add action-specific defaults
            if (
                entry["action_name"] in self._supported_actions
                and self._supported_actions[entry["action_name"]]["required"]
                is not None
            ):
                required_params = self._supported_actions[entry["action_name"]][
                    "required"
                ]
            else:
                required_params = {}

            # check for required parameters
            for param, expected_type in required_params.items():
                if param not in entry or not entry[param]:
                    msg = "[ERROR] Missing required {} {} parameter '{}'"
                    sys.exit(msg.format("actions", entry["action_name"], param))
                elif not isinstance(entry[param], eval(expected_type)):
                    msg = '[ERROR] Parameter "{}" in {} is of unexpected type: "{}" (expected: "{}")'
                    sys.exit(
                        msg.format(
                            entry["action_name"],
                            config_file,
                            type(entry[param]).__name__,
                            expected_type,
                        )
                    )

    def _get_args(self):
        """Parses input and returns arguments"""
        parser = ArgumentParser(
            description="Dynamically generates Snakefiles for data "
            "integration and machine learning pipelines."
        )

        parser.add_argument(
            "-c",
            "--config",
            help=(
                "Configuration filepath. (Will look for file named config.yml "
                "in current working directory, if none specified.)"
            ),
        )

        return parser

    def render(self):
        """Renders snakefile"""
        logging.info("Generating Snakefile...")

        # template search paths;
        # paths to inherited templates must be included here
        loaders = [
            PackageLoader("snakes", "templates"),
            PackageLoader("snakes", "templates/annotations"),
            PackageLoader("snakes", "templates/data"),
            PackageLoader("snakes", "templates/actions"),
            PackageLoader("snakes", "templates/actions/aggregate"),
            PackageLoader("snakes", "templates/actions/cluster"),
            PackageLoader("snakes", "templates/actions/filter"),
            PackageLoader("snakes", "templates/actions/impute"),
            PackageLoader("snakes", "templates/actions/load"),
            PackageLoader("snakes", "templates/actions/project"),
            PackageLoader("snakes", "templates/actions/transform"),
        ]

        # get jinaj2 environment
        env = Environment(
            loader=ChoiceLoader(loaders),
            trim_blocks=True,
            lstrip_blocks=True,
            extensions=["jinja2.ext.do"],
        )

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

        def action_subdir(action_name):
            """Returns the appropriate template sub-directory associated with a given action"""
            return action_name.split("_")[0]

        def log_debug(msg):
            """Logs a specified mesage using the logging module"""
            logging.debug(msg)
            return ""

        env.filters["basename"] = os.path.basename
        env.filters["basename_and_parent_dir"] = basename_and_parent_dir
        env.filters["basename_no_ext"] = basename_no_ext
        env.filters["expanduser"] = os.path.expanduser
        env.filters["is_list"] = is_list
        env.filters["replace_filename"] = replace_filename
        env.filters["action_subdir"] = action_subdir
        env.filters["debug"] = log_debug

        # get snakefile jinja2 template
        template = env.get_template("Snakefile")

        # root snakes script directory
        script_dir = os.path.abspath(resource_filename(__name__, "src"))

        # render template
        snakefile = template.render(
            config=self.config,
            wrangler=self._wrangler,
            date_str=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            script_dir=script_dir,
        )

        # save rendered snakefile to disk
        logging.info("Saving Snakefile to %s", self.output_file)

        with open(self.output_file, "w") as file_handle:
            file_handle.write(snakefile)
