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
    def __init__(self, output_dir, report_cfgs):
        """SnakeWrangler constructor"""
        self.output_dir = output_dir
        self.report_cfgs = report_cfgs

        self.datasets = {}
        self.reports = {}
        self.training_set = None
        self.feature_selection = []
        self.data_integration = []

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
            outfile = "/".join([self.output_dir, "data", dataset_name, "input.feather"])

            if kwargs["compression"] == "gzip":
                outfile = outfile + ".gz"

            rule = ActionRule(
                rule_id=rule_id,
                parent_id=None,
                input=kwargs["path"],
                output=outfile,
                local=True,
                template=template,
                inline=False,
            )

            # update parent id
            parent_id = rule_id

            # create OrderedDict and store load_data rule
            self.datasets[dataset_name] = OrderedDict({rule_id: rule})

            # if "input" meta-rule specified, check for requested reports to generate
            if actions[0]['action_name'] == 'input' and len(actions[0]['reports']) > 0:
                for report_name in actions[0]["reports"]:
                    self.add_report_rule(report_name, outfile, parent_id, **kwargs)

                del actions[0]

        # next, iterate over user-defined actions and add to wrangler
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
                output_filename = "{}.feather".format(rule_id)

            # determine output filepath to use
            if input.endswith(".gz"):
                output_filename = output_filename + ".gz"

            rule_output = os.path.join(os.path.dirname(input), output_filename)

            # drop unused filename params to clean up output
            if not action["filename"]:
                del action["filename"]

            # create new ActionRule or GroupedActionRule instance
            if action_name == "group":
                actions = action["actions"]
                del action["actions"]

                rule = GroupedActionRule(
                    rule_id, parent_id, actions, input, rule_output, **action
                )
            else:
                action_type = action_name.split("_")[0]
                template = "actions/{}/{}.snakefile".format(action_type, action_name)

                rule = ActionRule(
                    rule_id, parent_id, input, rule_output, template=template, **action
                )

            # add to dataset
            self.datasets[dataset_name][rule_id] = rule

            # update parent node
            parent_id = rule_id

            # if no report requested, stop here
            if len(action["reports"]) == 0:
                next

            # otherwise, iterate over reports and add relevant rules
            for report_name in action["reports"]:
                self.add_report_rule(report_name, rule_output, parent_id, **kwargs)

    def add_report_rule(self, report_name, rule_output, rule_id, **kwargs):
        """Add a single report rule to the pipeline"""
        # get report rule id
        report_id = f"report_{report_name}_{rule_id}"

        # get output filepath
        report_output = os.path.join(self.output_dir, "reports", f"{report_id}.html")

        # create new ReportRule instance and add to wrangler
        self.reports[report_id] = ReportRule(
            report_id,
            input=rule_output,
            output=report_output,
            rmd=self.report_cfgs[report_name]["rmd"],
            title="%s (%s)" % (self.report_cfgs[report_name]["title"], kwargs["name"]),
            name=kwargs["name"],
            metadata=kwargs["metadata"],
            styles=kwargs["styles"],
            theme="theme_bw"
        )

        # add any dependency rules of the report
        #  for action in self.report_cfgs[report_name]["depends"]:
        #      self.add_report_dependency_rule(dataset_name, report_name, report_id, rule_id, rule_output, action)

    #
    # Note: Aug 31, 2020
    #
    # Going to hold off adding report dependency support in this manner for now..
    #
    # It could be made to work, but it would require either including all dependency
    # action default parameter values in the reports config, or passing in the default
    # action configs from the renderer.
    #
    # Moreover, the current approach is limited to report dependencies, and doesn't
    # provide a mechanism to check if the needed data products have already been
    # explicitly generated.
    #
    # A better solution would be to impelement _generalized_ rule dependency support.
    #

    #  def add_report_dependency_rule(self, dataset_name, report_name, report_id, parent_id,
    #                                 rule_output, action):
    #      """Adds a report dependency rule to the pipeline"""
    #      if isinstance(action, str):
    #          action = {action: {}}
    #
    #      # determine action name, params, and template to use for report dependency
    #      action_name, action_params = list(action.items())[0]
    #      action_type = action_name.split("_")[0]
    #
    #      template = "actions/{}/{}.snakefile".format(action_type, action_name)
    #
    #      # rule name (ex. "report_general_eda_load_GSE106218_project_pca")
    #      rule_id = self._get_action_rule_id(report_id, action_name)
    #
    #      # determine output filepath
    #      #  if action["filename"] is not None:
    #      #      output_filename = action["filename"]
    #      #  else:
    #      output_filename = "{}.feather".format(rule_id)
    #      depend_output = os.path.join(os.path.dirname(rule_output), output_filename)
    #
    #      breakpoint()
    #
    #      rule = ActionRule(
    #          rule_id, parent_id, depend_output, template=template, **action
    #      )
    #
    #      # add to dataset
    #      self.datasets[dataset_name][rule_id] = rule

    def add_trainingset_rule(self, features, response, options):
        """Adds a training set-related SnakemakeRule"""
        # convert input feature and response rule ids to filepaths
        input = {"features": [], response: ""}

        for rule_id in features:
            input["features"].append(self.get_output(rule_id))

        # add response filepath to rule input list
        response_filepath = self.get_output(response)
        input["response"] = response_filepath

        output_dir = os.path.join(self.output_dir, "training_sets", "input")

        rule = MultiTrainingSetRule(input, output_dir, options)

        self.training_set = rule

    def add_feature_selection_rules(self, feature_selections):
        """Adds a training set-related SnakemakeRule"""
        # initial input from training set creation step
        input_dir = os.path.join(self.output_dir, "training_sets", "input")
        input = os.path.join(input_dir, "{training_set}.feather")

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
            filename = "{training_set}" + f"_{rule_id}.feather"

            output = pathlib.Path(input).parent.parent / "processed" / filename
            template = f"{fsel['method']}.snakefile"

            # create SnakemakeRule
            rule = FeatureSelectionRule(
                rule_id, input, output, template=template, **fsel
            )
            self.feature_selection.append(rule)

            input = output

    def add_data_integration_rules(self, data_integrations):
        """Adds a data integration-related SnakemakeRule"""
        # initial input from training set creation step
        # input_dir = os.path.join(self.output_dir, "training_sets", "input")
        # input = os.path.join(input_dir, "{training_set}.feather")
        for data_int in data_integrations:
            # determine unique snakemake rule name to use
            if "id" in data_int:
                rule_id = data_int["id"]
                del data_int["id"]

                # check to make sure user-specified id isn't already in use
                if rule_id in self.get_all_rule_ids():
                    sys.exit(
                        '[ERROR] data_integration id "{}" is already being used; '
                        "please choose a different name".format(rule_id)
                    )
            else:
                rule_id = self._get_data_integration_rule_id(data_int['datasets'], data_int["type"])

            # get input filepaths
            # TODO: validate existence of specified keys..
            inputs = [self.get_output(id_) for id_ in data_int['datasets']]
            del data_int['datasets']

            # determine output and template filepaths
            filename = f"{rule_id}.feather"
            output = os.path.join(self.output_dir, "data_integration", filename)

            template = f"integrate_{data_int['type']}.snakefile"
            del data_int['type']

            # create SnakemakeRule
            rule = DataIntegrationRule(
                rule_id, inputs, output, template=template, **data_int
            )
            self.data_integration.append(rule)

    def expand_dataset_paths(self):
        """
        Checks for rules with a 'dataset' parameter refering to the output from
        another rule and replaces the dataset id with the corresponding output path.
        """
        # expand action dataset parameters
        for dataset_name in self.datasets:
            for rule_id in self.datasets[dataset_name]:
                if "dataset" in self.datasets[dataset_name][rule_id].params:
                    output = self.get_output(
                        self.datasets[dataset_name][rule_id].params["dataset"]
                    )
                    self.datasets[dataset_name][rule_id].params["dataset"] = output

    def get_feature_selection_output(self):
        """Gets the output path for the last feature selection step"""
        # get output of final feature selection step
        if len(self.feature_selection) > 0:
            output = self.feature_selection[-1].output
        else:
            # if not feature selection was performed, use input training set
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

        # get terminal dataset rules
        for dataset_name in self.datasets:
            key = next(reversed(self.datasets[dataset_name]))
            out = self.datasets[dataset_name][key].output.replace(
                self.output_dir + "/", ""
            )
            terminal_rules.append(out)

        # add report rules
        for report in self.reports.values():
            out = report.output.replace(self.output_dir + "/", "")
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

    def _get_data_integration_rule_id(self, datasets, data_integration_type):
        """Determines a unique rule identifier to assign to a given data integration 
        rule"""
        # base rule id: <dataset1>...<datasetn>_<data_integration_type>
        rule_id = "_".join(datasets + [data_integration_type])

        # only allow letters, number, and underscores in rule names
        rule_id = re.sub(r"[^\w]", "_", rule_id)

        existing_ids = self.get_all_rule_ids()

        # if id is already being used, append first available numeric suffix
        id_counter = 2

        while rule_id in existing_ids:
            rule_id = "_".join([data_integration_type, str(id_counter)])
            rule_id = re.sub(r"[^\w]", "_", rule_id)
            id_counter += 1

        return rule_id

    def _get_action_rule_id(self, rule_prefix, rule_suffix):
        """Determines a unique rule identifier to assign to a given action"""
        # base rule id: <dataset_name>_<action>
        rule_id = rule_prefix + "_" + rule_suffix

        # only allow letters, number, and underscores in rule names
        rule_id = re.sub(r"[^\w]", "_", rule_id)

        existing_ids = self.get_all_rule_ids()

        # if id is already being used, append first available numeric suffix
        id_counter = 2

        while rule_id in existing_ids:
            rule_id = "_".join([rule_prefix, rule_suffix, str(id_counter)])
            rule_id = re.sub(r"[^\w]", "_", rule_id)
            id_counter += 1

        return rule_id

    def get_all_rule_ids(self):
        """Returns a list of all rule ids currently being used"""
        ids = []

        for dataset_name in self.datasets:
            ids = ids + list(self.datasets[dataset_name].keys())

        ids = ids + list(self.reports.keys())

        return ids

    def get_output(self, target_id):
        """Returns the output filepath associated with a given rule_id"""
        for dataset_name in self.datasets:
            for rule_id in self.datasets[dataset_name]:
                if rule_id == target_id:
                    return self.datasets[dataset_name][rule_id].output

