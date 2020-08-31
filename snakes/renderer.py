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
import pandas as pd
from argparse import ArgumentParser
from jinja2 import Environment, ChoiceLoader, PackageLoader
from pkg_resources import resource_filename
from snakes.util import load_data, recursive_update
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

        # load supported reports
        with open(os.path.join(self._conf_dir, "reports.yml")) as fp:
            self._report_cfgs = yaml.load(fp, Loader=yaml.FullLoader)

            # root snakes report directory
            report_dir = os.path.abspath(resource_filename(__name__, "reports"))

            # add report path prefixed
            for report in self._report_cfgs:
                self._report_cfgs[report]['rmd'] = os.path.join(report_dir,
                                                                self._report_cfgs[report]['rmd'])

        # load feature selection required / default parameters
        with open(os.path.join(self._conf_dir, "feature_selection.yml")) as fp:
            self._supported_feat_sel_methods = yaml.load(fp, Loader=yaml.FullLoader)

        # load data integration required / default parameters
        with open(os.path.join(self._conf_dir, "data_integration.yml")) as fp:
            self._supported_data_int_types = yaml.load(fp, Loader=yaml.FullLoader)

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
        output_dir = os.path.join(
            os.path.expanduser(self.config["output_dir"]), self.config["version"]
        )

        self._wrangler = SnakeWrangler(output_dir, self._report_cfgs)

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

        # validate and parse training sets configuration
        if "features" in self.config["training_sets"]:
            self._validate_training_sets_config()

            self._wrangler.add_trainingset_rule(
                self.config["training_sets"]["features"],
                self.config["training_sets"]["response"],
                self.config["training_sets"]["options"],
            )

        # validate and parse feature selection configuration
        if len(self.config["feature_selection"]) > 0:
            fsel_cfgs = []

            for fsel_cfg in self.config["feature_selection"]:
                fsel_cfgs.append(self._parse_feature_selection_config(fsel_cfg))

            # TODO
            # self._validate_feature_selection_config()
            self.config["feature_selection"] = fsel_cfgs

            self._wrangler.add_feature_selection_rules(fsel_cfgs)

        # validate and parse data integration configuration
        if len(self.config["data_integration"]) > 0:
            data_int_cfgs = []

            for data_int_cfg in self.config["data_integration"]:
                data_int_cfgs.append(self._parse_data_integration_config(data_int_cfg))

            # TODO
            # self._validate_data_integration_config()
            self.config["data_integration"] = data_int_cfgs

            self._wrangler.add_data_integration_rules(data_int_cfgs)

        # expand paths for any dataset parameters
        self._wrangler.expand_dataset_paths()

    def _parse_dataset_config(self, user_cfg):
        """Loads a dataset config file and overides any global settings with any dataset-specific ones."""

        # default dataset parameters
        # TODO: move to conf/
        dataset = {
            "file_type": "",
            "compression": None,
            "encoding": "utf-8",
            "path": "",
            "name": "",
            "xid": "x",
            "yid": "y",
            "sep": "",
            "sheet": 0,
            "config_file": "",
            "index_col": 0,
            "metadata": {
                "columns": "",
                "rows": ""
            },
            "styles": {
                "columns": {
                    "color": []
                },
                "rows": {
                    "color": []
                }
            },
            "actions": []
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
            if ext in [".csv", ".txt", ".tsv", ".tab"]:
                # comma-separated / tab-delmited
                dataset["file_type"] = "csv"
            elif ext in [".xls", ".xlsx"]:
                # excel spreadsheet
                dataset["file_type"] = "xls"
            elif ext in [".feather"]:
                dataset["file_type"] = "feather"
            elif ext in [".parquet"]:
                dataset["file_type"] = "parquet"
            else:
                msg = "Config error: could not determine appropriate file_type for {}"
                sys.exit(msg.format(dataset["path"]))

        # determine delimiter for csv/tsv files
        if dataset["file_type"] == "csv" and dataset["sep"] == "":
            if ext in [".csv"]:
                dataset["sep"] = ","
            elif ext in [".tsv", ".tab", ".txt"]:
                dataset["sep"] = "\t"

        # compression flag for csv/tsv files
        # for feather/parquet input datasets compression does not need to be specified
        if dataset["path"].endswith("gz"):
            dataset["compression"] = "gzip"

        # if a str index column value is specified, wrap in quotation marks so that it is handled
        # properly in templates
        if isinstance(dataset["index_col"], str):
            dataset["index_col"] = "'{}'".format(dataset["index_col"])

        # parse actions section config section
        dataset["actions"] = self._parse_actions_list(
            dataset["actions"], dataset["name"]
        )

        # if nothing is specified in config file, generate report plots using all
        # relevant metadata fields as stylistic elements
        self._check_styles(dataset)

        # validate dataset config
        self._validate_dataset_config(dataset)

        # separate actions from rest of dataset parameters
        dataset_actions = dataset["actions"]

        del dataset["actions"]

        # add actions to SnakeWrangler instance
        self._wrangler.add_actions(dataset["name"], dataset_actions, **dataset)

        # store parsed dataset config
        return dataset

    def _check_styles(self, dataset):
        """Checks to see if style settings are specified in dataset config, and if not,
        uses all available metadata fields as such."""
        # check column styles
        if dataset['styles']['columns']['color'] ==  []:
            if dataset['metadata']['columns'] != '':
                mdat = load_data(dataset['metadata']['columns'])
                dataset['styles']['columns']['color'] = mdat.columns[mdat.nunique() > 1].tolist()

        # check row styles
        if dataset['styles']['rows']['color'] ==  []:
            if dataset['metadata']['rows'] != '':
                mdat = load_data(dataset['metadata']['rows'])
                dataset['styles']['rows']['color'] = mdat.rows[mdat.nunique() > 1].tolist()

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
        parameters), and dicts (i.e. "{'action_name': { params }}").

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
        # "branch" meta-action
        elif action_name == "branch":
            return self._parse_actions_list(action_params, dataset_name)
        # "input" meta-action
        #  elif action_name == "input":
        #      breakpoint()

        # check to make sure parameters specified as a dict (in case user accidentally uses
        # a list in the yaml)
        if type(action_params) != dict:
            msg = "Config error: parameters for {} must be specified as a YAML dictionary."
            sys.exit(msg.format(action_name))

        # get default action params
        cfg = {
            "action_name": action_name,
            "filename": None,
            "inline": True,
            "local": False,
            "reports": []
        }

        if action_name in self._supported_actions:
            cfg.update(self._supported_actions[action_name]["defaults"])

        # overide with any user-specified config values
        cfg.update(action_params)

        return cfg

    def _parse_feature_selection_config(self, fsel_cfg):
        """Parses a single feature selection config section"""
        # if no parameters specified, add placeholder empty dict
        if isinstance(fsel_cfg, str):
            fsel_cfg = {fsel_cfg: {}}

        # split into feature selection method and parameters
        fsel_method, fsel_params = list(fsel_cfg.items())[0]

        # check to make sure parameters specified as a dict (in case user accidentally uses
        # a list in the yaml)
        if type(fsel_params) != dict:
            msg = "Config error: parameters for {} must be specified as a YAML dictionary."
            sys.exit(msg.format(fsel_method))

        # get default feature selection params
        cfg = {"method": fsel_method}

        if fsel_method in self._supported_feat_sel_methods:
            cfg.update(self._supported_feat_sel_methods[fsel_method]["defaults"])

        # overide with any user-specified config values
        cfg.update(fsel_params)

        return cfg

    def _parse_data_integration_config(self, data_int_cfg):
        """Parses a single feature selection config section"""
        # split into feature selection type and parameters
        data_int_type, data_int_params = list(data_int_cfg.items())[0]

        # check to make sure parameters specified as a dict (in case user accidentally uses
        # a list in the yaml)
        if type(data_int_params) != dict:
            msg = "Config error: parameters for {} must be specified as a YAML dictionary."
            sys.exit(msg.format(data_int_type))

        # get default feature selection params
        cfg = {"datasets": [], "type": data_int_type}

        if data_int_type in self._supported_data_int_types:
            cfg.update(self._supported_data_int_types[data_int_type]["defaults"])

        # overide with any user-specified config values
        cfg.update(data_int_params)

        return cfg

    def _validate_main_config(self):
        """Performs some basic check on config dict to make sure required settings are present."""
        #  check for required top-level parameters in main config
        required_params = {"name": str, "version": str, "datasets": list}

        for param, expected_type in required_params.items():
            if param not in self.config:
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
            if param not in dataset_cfg:
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
        # TODO Aug 18: check to make sure only valid report names specified
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
            elif entry["action_name"] == "input":
                # skip validation for "input" meta-action, if present
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
                if param not in entry:
                    msg = "[ERROR] Missing required parameter '{}' for {}"
                    breakpoint()
                    sys.exit(msg.format(param, entry["action_name"]))
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

    def _validate_training_sets_config(self):
        """Validates the training sets section of config file"""
        # check for required subsections
        for key in ["features", "response"]:
            if key not in self.config["training_sets"]:
                msg = "[ERROR] Missing required training_sets parameter '{}'"
                sys.exit(msg.format(key))

        # check to make sure valid target ids specified
        target_ids = self.config["training_sets"]["features"] + [
            self.config["training_sets"]["response"]
        ]

        rule_ids = self._wrangler.get_all_rule_ids()

        for target_id in target_ids:
            if target_id not in rule_ids:
                msg = "[ERROR] Unknown target action id specified: '{}'"
                sys.exit(msg.format(target_id))

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
            PackageLoader("snakes", "templates/actions"),
            PackageLoader("snakes", "templates/feature_selection"),
            PackageLoader("snakes", "templates/gene_sets"),
            PackageLoader("snakes", "templates/training_set"),
            PackageLoader("snakes", "templates/actions/aggregate"),
            PackageLoader("snakes", "templates/actions/cluster"),
            PackageLoader("snakes", "templates/actions/filter"),
            PackageLoader("snakes", "templates/actions/integrate"),
            PackageLoader("snakes", "templates/actions/impute"),
            PackageLoader("snakes", "templates/actions/load"),
            PackageLoader("snakes", "templates/actions/map"),
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
        env.filters["basename"] = os.path.basename
        env.filters["expanduser"] = os.path.expanduser

        # get snakefile jinja2 template
        template = env.get_template("Snakefile")

        # root snakes script directory
        script_dir = os.path.abspath(resource_filename(__name__, "src"))

        # root data directory
        data_dir = os.path.abspath(resource_filename(__name__, "data"))

        # render template
        snakefile = template.render(
            config=self.config,
            wrangler=self._wrangler,
            date_str=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            script_dir=script_dir,
            data_dir=data_dir
        )

        # save rendered snakefile to disk
        logging.info("Saving Snakefile to %s", self.output_file)

        with open(self.output_file, "w") as file_handle:
            file_handle.write(snakefile)
