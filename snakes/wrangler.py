"""
SnakeWrangler class definition

The SnakeWrangler class handles the mapping between Snakes configuration entries
to Snakemake rules.

Each Snakes action and training set is associated with a unique identifier which is used
for cross-references, as well as rule name generation.

This class provides helps to manage these elements and provide helper functions for
determining the rulenames, input and output filepaths, and associated parameters.
"""
import os
import re
import sys
import pandas as pd
import pathlib
from collections import OrderedDict
from snakes.rules import *


class SnakeWrangler:
    def __init__(self, output_dir):
        """SnakeWrangler constructor"""
        self.output_dir = output_dir

        self.datasets = {}
        self.training_set = None
        self.feature_selection = []

    def add_actions(self, dataset_name, actions, parent_id=None, **kwargs):
        """
        Adds one or more actions to a specified dataset pipeline.

        Parameters
        ----------
        dataset_name: str
            Name of the dataset to add actions to
        actions: list
            A nested list of actions to be added
        parent_id: str
            Identifier for the parent rule of the rule(s) being passed in.
        """
        # if dataset has not yet been added, create a new OrderedDict instance and
        # add initial load_data rule
        if dataset_name not in self.datasets:
            # create load_data snakemake rule
            rule_id = "load_{}".format(dataset_name)

            # determine template filepath
            template_filename = "load_{}".format(kwargs["file_type"])
            template = "actions/load/{}.snakefile".format(template_filename)

            # determine output filepath to use
            outfile = "/".join([self.output_dir, "data", dataset_name, "raw.csv"])

            if kwargs["compression"] == "gzip":
                outfile = outfile + ".gz"

            rule = ActionRule(
                rule_id=rule_id,
                parent_id=None,
                input=kwargs["path"],
                output=outfile,
                local=True,
                template=template,
                groupable=False,
            )

            # update parent id
            parent_id = rule_id

            # create OrderedDict and store load_data rule
            self.datasets[dataset_name] = OrderedDict({rule_id: rule})

        # iterate over user-defined actions and add to wrangler
        for action in actions:
            # dataset branch
            if isinstance(action, list):
                self.add_actions(dataset_name, action, parent_id=parent_id, **kwargs)
                continue

            # get action name
            action_name = action["action_name"]
            del action["action_name"]

            # determine unique snakemake rule name to use
            if "id" in action:
                rule_id = action["id"]
                del action["id"]

                # check to make sure user-specified id isn't already in use
                if rule_id in self.get_all_rule_ids():
                    sys.exit(
                        '[ERROR] Action id "{}" is already being used; '
                        "please choose a different name".format(rule_id)
                    )
            else:
                rule_id = self._get_action_rule_id(dataset_name, action_name)

            # determine input filepath
            input = self.get_output(parent_id)

            # determine output filepath
            if action["filename"] is not None:
                output_filename = action["filename"]
            else:
                output_filename = "{}.csv".format(rule_id)

            # determine output filepath to use
            if input.endswith(".gz"):
                output_filename = output_filename + ".gz"

            output = os.path.join(os.path.dirname(input), output_filename)

            # drop unused filename params to clean up output
            if not action["filename"]:
                del action["filename"]

            # if action includes a 'dataset' argument, expand to full path
            if "dataset" in action:
                action["dataset"] = self.get_output(action["dataset"])

            # create new ActionRule or GroupedActionRule instance
            if action_name == "group":
                rule = GroupedActionRule(
                    rule_id, parent_id, action["actions"], input, output, **action
                )
            else:
                action_type = action_name.split("_")[0]
                template = "actions/{}/{}.snakefile".format(action_type, action_name)

                rule = ActionRule(
                    rule_id, parent_id, input, output, template=template, **action
                )

            # add to dataset
            self.datasets[dataset_name][rule_id] = rule

            # update parent node
            parent_id = rule_id

    def add_trainingset_rule(self, features, response, options):
        """Adds a training set-related SnakemakeRule"""
        # convert input feature and response rule ids to filepaths
        input = {"features": [], response: ""}

        for rule_id in features:
            input["features"].append(self.get_output(rule_id))

        # add response filepath to rule input list
        response_filepath = self.get_output(response)
        input["response"] = response_filepath

        output_dir = os.path.join(self.output_dir, "training_sets", "raw")

        rule = MultiTrainingSetRule(input, output_dir, options)

        self.training_set = rule

    def add_feature_selection_rules(self, feature_selections):
        """Adds a training set-related SnakemakeRule"""
        # initial input from training set creation step
        input_dir = os.path.join(self.output_dir, "training_sets", "raw")
        input = os.path.join(input_dir, "{training_set}.csv")

        for fsel in feature_selections:
            # determine unique snakemake rule name to use
            if "id" in fsel:
                rule_id = fsel["id"]
                del fsel["id"]

                # check to make sure user-specified id isn't already in use
                if rule_id in self.get_all_rule_ids():
                    sys.exit(
                        '[ERROR] feature_selection id "{}" is already being used; '
                        "please choose a different name".format(rule_id)
                    )
            else:
                rule_id = self._get_feature_selection_rule_id(fsel["method"])

            # determine output and template filepaths
            filename = "{training_set}" + f"_{rule_id}.csv"

            output = pathlib.Path(input).parent.parent / "processed" / filename
            template = f"{fsel['method']}.snakefile"

            # create SnakemakeRule
            rule = FeatureSelectionRule(
                rule_id, input, output, template=template, **fsel
            )
            self.feature_selection.append(rule)

            input = output

    def get_feature_selection_output(self):
        """Gets the output path for the last feature selection step"""
        # get output of final feature selection step
        if len(self.feature_selection) > 0:
            output = self.feature_selection[-1].output
        else:
            # if not feature selection was performed, use raw training set
            output = self.training_set.output

        return output

    def get_localrules(self):
        """Returns a list of all rules which should be run locally"""
        localrules = []

        for dataset_name in self.datasets:
            for rule_id in self.datasets[dataset_name]:
                if self.datasets[dataset_name][rule_id].local:
                    localrules.append(rule_id)

        return ", ".join(localrules)

    def get_terminal_rules(self):
        """Returns a list of the final rules in each dataset-specific pipeline"""
        terminal_rules = []

        for dataset_name in self.datasets:
            key = next(reversed(self.datasets[dataset_name]))
            out = self.datasets[dataset_name][key].output.replace(
                "{}/data/".format(self.output_dir), ""
            )
            terminal_rules.append(out)

        return "['{}']".format("', '".join(terminal_rules))

    def _get_feature_selection_rule_id(self, feat_selection_method):
        """Determines a unique rule identifier to assign to a given feature selection
        rule"""
        # base rule id: <feature_selection_method>
        rule_id = feat_selection_method

        # only allow letters, number, and underscores in rule names
        rule_id = re.sub(r"[^\w]", "_", rule_id)

        existing_ids = self.get_all_rule_ids()

        # if id is already being used, append first available numeric suffix
        id_counter = 2

        while rule_id in existing_ids:
            rule_id = "_".join([feat_selection_method, str(id_counter)])
            rule_id = re.sub(r"[^\w]", "_", rule_id)
            id_counter += 1

        return rule_id

    def _get_action_rule_id(self, dataset_name, action_name):
        """Determines a unique rule identifier to assign to a given action"""
        # base rule id: <dataset_name>_<action>
        rule_id = dataset_name + "_" + action_name

        # only allow letters, number, and underscores in rule names
        rule_id = re.sub(r"[^\w]", "_", rule_id)

        existing_ids = self.get_all_rule_ids()

        # if id is already being used, append first available numeric suffix
        id_counter = 2

        while rule_id in existing_ids:
            rule_id = "_".join([dataset_name, action_name, str(id_counter)])
            rule_id = re.sub(r"[^\w]", "_", rule_id)
            id_counter += 1

        return rule_id

    def get_all_rule_ids(self):
        """Returns a list of all rule ids currently being used"""
        ids = []

        for dataset_name in self.datasets:
            ids = ids + list(self.datasets[dataset_name].keys())

        return ids

    def get_output(self, target_id):
        """Returns the output filepath associated with a given rule_id"""
        for dataset_name in self.datasets:
            for rule_id in self.datasets[dataset_name]:
                if rule_id == target_id:
                    return self.datasets[dataset_name][rule_id].output
