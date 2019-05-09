"""
SnakeWrangler class definition

The SnakeWrangler class handles the mapping between Snakes action configuration entries
to Snakemake rules.

Each Snakes action is associated with a unique identifier which is used for
cross-references, as well as rule name generation.

This class provides helps to manage these actions and provide helper functions for
determining the rulenames, input and output filepaths, and parameters associated with
each action.
"""
import os
import re
import sys
from collections import OrderedDict
from snakes.actions import SnakesAction, SnakesActionGroup


class SnakeWrangler:
    def __init__(self, output_dir):
        """SnakeWrangler constructor"""
        self.output_dir = output_dir
        self.datasets = {}
        self.counters = OrderedDict()

    # def add(self, dataset, input_file, file_type, actions, parent_id=None, **kwargs):
    def add(self, dataset_name, actions, parent_id=None, **kwargs):
        """
        Adds one or more steps to a specified dataset.

        Parameters
        ----------
        dataset_name: str
            Name of the dataset to add actions to
        actions: list
            A nested list of actions to be added
        parent_id: str
            Identifier for the parent action of the action(s) being passed in.
        """
        # if dataset has not yet been added, create a new OrderedDict instance and
        # add initial load_data action
        if dataset_name not in self.datasets:
            # create load_data action
            action_id = "load_{}".format(dataset_name)

            snakes_action = SnakesAction(
                action_name="load_{}".format(kwargs["file_type"]),
                action_id=action_id,
                parent_id=None,
                input=kwargs["path"],
                output="/".join([self.output_dir, "data", dataset_name, "raw.csv"]),
                groupable=False,
            )

            # update parent id
            parent_id = action_id

            # create OrderedDict and store load_data action
            self.datasets[dataset_name] = OrderedDict({action_id: snakes_action})

        # iterate over user-defined actions and add to wrangler
        for action in actions:
            # dataset branch
            if isinstance(action, list):
                self.add(dataset_name, action, parent_id=parent_id, **kwargs)
                continue

            # get action name
            action_name = action["action_name"]
            del action["action_name"]

            # determine unique action identifier / snakemake rule name to use
            if "id" in action:
                action_id = action["id"]
                del action["id"]

                # check to make sure user-specified id isn't already in use
                if action_id in self._get_all_action_ids():
                    sys.exit(
                        '[ERROR] Action id "{}" is already being used; '
                        "please choose a different name".format(action_id)
                    )
            else:
                action_id = self._get_action_id(dataset_name, action_name)

            # determine input filepath
            input = self._get_output(parent_id)

            # determine output filepath
            if action["filename"] is not None:
                output_filename = action["filename"]
            else:
                output_filename = "{}.csv".format(action_id)

            output = os.path.join(os.path.dirname(input), output_filename)

            # drop unused filename params to clean up output
            if not action["filename"]:
                del action["filename"]

            # create new SnakesAction or SnakesActionGroup instance
            if action_name == "group":
                snakes_action = SnakesActionGroup(
                    action_id, parent_id, action["actions"], input, output, **action
                )
            else:
                snakes_action = SnakesAction(
                    action_name, action_id, parent_id, input, output, **action
                )

            # add to dataset
            self.datasets[dataset_name][action_id] = snakes_action

            # if this is the first action in the dataset, point counter to it
            if len(self.datasets[dataset_name]) == 1:
                self.counters[dataset_name] = action_id

            # update parent node
            parent_id = action_id

    def _get_action_id(self, dataset_name, action_name):
        """Determines a unique action identifier to assign to a given action"""
        # base action id: <dataset_name>_<action>
        action_id = dataset_name + "_" + action_name

        # only allow letters, number, and underscores in rule names
        action_id = re.sub(r"[^\w]", "_", action_id)

        existing_ids = self.datasets[dataset_name].keys()

        # if id is already being used, append first available numeric suffix
        id_counter = 2

        while action_id in existing_ids:
            action_id = "_".join([dataset_name, action_name, str(id_counter)])
            id_counter += 1

        return action_id

    def _get_all_action_ids(self):
        """Returns a list of all action ids currently being used"""
        return [self.datasets[dataset_name].keys() for dataset_name in self.datasets]

    def _get_output(self, target_id):
        """Returns the output filepath associated with a given action_id"""
        for dataset_name in self.datasets:
            for action_id in self.datasets[dataset_name]:
                if action_id == target_id:
                    return self.datasets[dataset_name][action_id].output
