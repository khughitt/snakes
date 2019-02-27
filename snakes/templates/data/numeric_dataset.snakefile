################################################################################
#
# {% block header_comment %}
# Generic Numeric Dataset workflow
# {% endblock %}
#
################################################################################
{#############################################################################################}
{# Below we define a custom namespace which is used to keep track of the most recent rule
{# included for the dataset. The namespace approach is required so that variables can be
{# modified in the scope of a jinja for loop.
{#############################################################################################}
{% set ns = namespace(found=false) %}

{# initial input and output filepaths #}
{% set ns.cur_input  =  data_source.path %}
{% set ns.cur_output =  '/'.join([output_dir, 'data', data_source.name, 'raw.csv']) %}
#
# Load raw data
#
{% set rule_name = 'load_' ~ data_source.name | to_rule_name %}
{% do simple_rules.append(rule_name) %}
rule {{ rule_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
    run:
        # for now, assume that all input files are provided in csv or tsv format with a
        # header and a column for row ids
        pd.read_table(input[0], sep='{{ data_source.sep }}', index_col={{ data_source.index_col }}).to_csv(output[0], index_label='{{ data_source.xid }}')

{% if data_source.pipeline | length > 0 %}
#
# {{ data_source.name }} actions
#
{% for action in data_source.pipeline recursive %}
    {% if action | is_list %}
{{ loop(action) }}
    {% else %}
        {% set ns.cur_input  = ns.cur_output %}
        {% set ns.cur_output =  ns.cur_input | replace_filename(action.action + '.csv') %}
rule {{ action.rule_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
{% include 'pipeline/' + action.action + '.snakefile' %}
    {% endif %}
{% endfor %}
{% endif %}

{# Keep track of last version of file processed #}
{% do training_set_inputs.append(ns.cur_output | basename_and_parent_dir) -%}
