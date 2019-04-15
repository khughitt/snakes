################################################################################
#
# {{ dataset.name }} workflow
#
################################################################################
{#############################################################################################}
{# Below we define a custom namespace which is used to keep track of the most recent rule
{# included for the dataset. The namespace approach is required so that variables can be
{# modified in the scope of a jinja for loop.
{#############################################################################################}
{% set ns = namespace(found=false) %}

{# initial input and output filepaths #}
{% set ns.cur_input  =  dataset.path %}
{% set ns.cur_output =  '/'.join([output_dir, dataset.name, 'data', dataset.name ~ '_raw.csv']) %}
#
# Load {{ dataset.name }} data
#
{% set rule_name = 'load_' ~ dataset.name | to_rule_name %}
{% do simple_rules.append(rule_name) %}
rule {{ rule_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
    run:
{% block load_data %}{% endblock %}
{% if config.development.enabled and config.development.sample_row_frac < 1 %}
        # sub-sample dataset rows
        dat = dat.sample(frac={{ config.development.sample_row_frac }}, random_state={{ config.random_seed }}, axis=0)
{% endif %}
{% if config.development.enabled and config.development.sample_col_frac < 1 %}
        # sub-sample dataset columns
        dat = dat.sample(frac={{ config.development.sample_col_frac }}, random_state={{ config.random_seed }}, axis=1)
{% endif %}
        dat.to_csv(output[0], index_label='{{ dataset.xid }}')
{% if dataset.actions | length > 0 %}
#
# {{ dataset.name }} actions
#
{% for action in dataset.actions recursive %}
    {# recurse on pipeline branches #}
    {# parent_output used to preserve last output filename prior to recursion. #}
    {% if action | is_list %}
    {% set parent_output = ns.cur_output %}
{{ loop(action) }}
    {% set ns.cur_output = parent_output %}
    {% else %}
        {% if action.file != '' %}
        {% set output_filename = action.file %}
        {% else %}
        {% set output_filename = dataset.name ~ '_' ~ action.action ~ '.csv' %}
        {% endif %}
        {% set ns.cur_input  = ns.cur_output %}
        {% set ns.cur_output =  ns.cur_input | replace_filename(output_filename) %}
rule {{ action.rule_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
{% include 'actions/' + action.action | action_subdir + "/" + action.action + '.snakefile' %}
    {% endif %}
{% endfor %}
{% endif %}

{# Keep track of last version of file processed #}
{% do training_set_inputs.append(dataset.name ~ '/' ~ ns.cur_output | basename_and_parent_dir) -%}
