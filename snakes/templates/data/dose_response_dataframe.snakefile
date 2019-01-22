################################################################################
#
# {% block header_comment %}Dose Response Curve Data
{% endblock %}
#
################################################################################
{############################################################################################-#}
{# Below we define a custom namespace which is used to keep track of the most recent rule    -#}
{# included for the dataset. The namespace approach is required so that variables can be     -#}
{# modified in the scope of a jinja for loop.                                                -#}
{############################################################################################-#}
{% set ns = namespace(found=false) %}
{# initial input and output filepaths #}
{% set ns.cur_input  =  data_source.path %}
{% set ns.cur_output =  '/'.join([output_dir, 'data', data_source.name, 'raw.csv']) %}

{# create a list of the columns that are used in the analysis -#}
{% set required_fields = [data_source.sample_id, data_source.compound_id, data_source.response_var] %}
{% for action in data_source.pipeline %}
    {% if 'field' in action %}
        {% do required_fields.append(action.field) %}
    {% endif %}
{% endfor %}
#
# Load raw curve data
#
{% set rule_name = 'load_' ~ data_source.name | to_rule_name %}
{% do simple_rules.append(rule_name) %}
rule {{ rule_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
    run:
        # for now, assume that all input files are provided in csv format with a
        # header and a column for row ids
        dat = pd.read_table(input[0], sep='{{ data_source["sep"] }}', index_col={{ data_source.index_col }})

        # create a list of the relevant fields to keep
        fields_to_keep = {{ required_fields | unique | list }}
        fields_to_keep = [x for x in fields_to_keep if x != dat.index.name]

        # drop unneeded fields and store result
        dat[fields_to_keep].to_csv(output[0])

{% if data_source.pipeline | length > 0 %}
#
# Data transformations and filters
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

{# Keep track of last version of file processed -#}
{% do training_set_inputs.append(ns.cur_output | basename_and_parent_dir) -%}
