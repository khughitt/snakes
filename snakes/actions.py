"""SnakesAction class definition"""
import os
from collections import OrderedDict


class SnakesAction:
    def __init__(
        self,
        action_name,
        action_id,
        parent_id,
        input,
        output,
        groupable=True,
        local=False,
        **kwargs
    ):
        """Creates a new SnakesAction instance from a dict representation"""
        self.action_name = action_name
        self.action_id = action_id
        self.parent_id = parent_id
        self.input = input
        self.output = output
        self.groupable = groupable
        self.local = local
        self.params = kwargs

        # determine template filepath
        action_type = action_name.split("_")[0]
        self.template = "actions/{}/{}.snakefile".format(action_type, action_name)

    def __repr__(self):
        """Prints a string representation of SnakesAction instance"""
        template = """
        SnakesAction ({})
        
        - action_name : {}
        - parent_id   : {}
        - input       : {}
        - output      : {}
        - groupable   : {}
        - local       : {}
        - params      : {}
        """

        return template.format(
            self.action_id,
            self.action_name,
            self.parent_id,
            self.input,
            self.output,
            self.groupable,
            self.local,
            self.params,
        )


class SnakesActionGroup:
    def __init__(
        self, action_id, parent_id, group_actions, input, output, local=False, **kwargs
    ):
        """Creates a new SnakesActionGroup instance from a dict representation"""
        self.action_name = "group"
        self.action_id = action_id
        self.parent_id = parent_id
        self.input = input
        self.output = output
        self.local = local
        self.params = kwargs

        # load sub-actions
        self.actions = OrderedDict()

        for action in group_actions:
            # get action name
            action_name = action["action_name"]
            del action["action_name"]

            # create new SnakesAction instance
            self.actions[action_name] = SnakesAction(
                action_name,
                action_id=None,
                parent_id=None,
                input=None,
                output=None,
                **action
            )
