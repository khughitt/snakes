"""SnakemakeRule and SnakemakeRuleGroup class definitions"""
import os
from collections import OrderedDict


class SnakemakeRule:
    def __init__(
        self, rule_id, parent_id, input, output, local=False, template=None, **kwargs
    ):
        """Creates a new SnakemakeRule instance from a dict representation"""
        self.rule_id = rule_id
        self.parent_id = parent_id
        self.input = input
        self.output = output
        self.local = local
        self.template = template
        self.params = kwargs

    def __repr__(self):
        """Prints a string representation of SnakemakeRule instance"""
        template = """
        SnakemakeRule ({})
        
        - parent_id   : {}
        - input       : {}
        - output      : {}
        - local       : {}
        - template    : {}
        - params      : {}
        """

        return template.format(
            self.rule_id,
            self.parent_id,
            self.input,
            self.output,
            self.local,
            self.template,
            self.params,
        )


class ActionRule(SnakemakeRule):
    def __init__(
        self,
        rule_id,
        parent_id,
        input,
        output,
        groupable=True,
        local=False,
        template=None,
        **kwargs
    ):
        """Creates a new SnakemakeRule instance from a dict representation"""
        super().__init__(rule_id, parent_id, input, output, local, template, **kwargs)

        self.groupable = groupable
        self.groupped = False

    def __repr__(self):
        """Prints a string representation of SnakemakeRule instance"""

        template = """
        - groupable   : {}
        """

        return super().__repr__() + template.format(self.groupable)


class TrainingSetRule(SnakemakeRule):
    def __init__(self, input, output, local=False):
        """Creates a new SnakemakeRule instance from a dict representation"""
        super().__init__(
            "create_training_set",
            None,
            input,
            output,
            local,
            "single_training_set.snakefile",
        )


class MultiTrainingSetRule(SnakemakeRule):
    def __init__(self, input, output, options, local=False):
        """Creates a new SnakemakeRule instance from a dict representation"""
        super().__init__(
            "create_training_set",
            None,
            input,
            output,
            local,
            "multi_training_set.snakefile",
        )
        self.options = options


class GroupedActionRule:
    def __init__(
        self, rule_id, parent_id, group_actions, input, output, local=False, **kwargs
    ):
        """Creates a new SnakemakeRuleGroup instance from a dict representation"""
        self.rule_id = rule_id
        self.parent_id = parent_id
        self.input = input
        self.output = output
        self.local = local
        self.params = kwargs

        self.groupped = True

        # load sub-actions
        self.actions = OrderedDict()

        for action in group_actions:
            # get action name
            action_name = action["action_name"]
            del action["action_name"]

            # determine template filepath
            action_type = action_name.split("_")[0]
            template = "actions/{}/{}.snakefile".format(action_type, action_name)

            # create new SnakemakeRule instance
            self.actions[action_name] = ActionRule(
                rule_id=None,
                parent_id=None,
                input=None,
                output=None,
                template=template,
                **action
            )
