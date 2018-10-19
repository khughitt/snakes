################################################################################
#
# {% block header_comment %}
# Generic Numeric Dataset workflow
# {% endblock %}
#
################################################################################
{############################################################################################-#}
{# Below we define a custom namespace which is used to keep track of the most recent rule
{# included for the dataset. The namespace approach is required so that variables can be
{# modified in the scope of a jinja for loop.
{############################################################################################-#}
{% set ns = namespace(found=false) %}
{% set ns.cur_input  =  dataset_params['path'] -%}
{% set ns.cur_output =  '/'.join([output_dir, 'data', dataset_params['name'], 'raw.csv']) -%}
#
# Load raw data
{% set rule_name = 'read_' ~ dataset_params['name'] | to_rule_name -%}
{% do local_rules.append(rule_name) -%}
rule {{ rule_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
    run:
        # for now, assume that all input files are provided in csv format with a
        # header and a column for row ids
        pd.read_csv(input[0], index_col=0).to_csv(output[0], index_label='{{ dataset_params["xid"] }}')

{% if 'filters' in dataset_params -%}
#
# Data filtering
#
{% for filter_name, filter_params in dataset_params['filters'].items() -%}
    {% set ns.cur_input  = ns.cur_output -%}
    {% set ns.cur_output =  ns.cur_input | replace_filename('filter_' + filter_name + '.csv') -%}
{% set rule_name = dataset_params['name'] ~ '_filter_' ~ filter_name | to_rule_name -%}
{% do local_rules.append(rule_name) -%}
rule {{ rule_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
{% include 'filters/' + filter_params['type'] + '.snakefile' %}

{% endfor %}
{% endif -%}

{% if 'transforms' in dataset_params -%}
#
# Data transformations
#
{% for transform in dataset_params['transforms'] -%}
    {% set ns.cur_input  = ns.cur_output -%}
    {% set ns.cur_output =  ns.cur_input | replace_filename('transform_' + transform + '.csv') -%}
{% set rule_name = dataset_params['name'] ~ '_' ~ transform ~ '_transform' | to_rule_name -%}
{% do local_rules.append(rule_name) -%}
rule {{ rule_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
{% include 'transforms/' + transform + '.snakefile' %}

{% endfor %}
{% endif -%}

#
# Saved cleaned dataset
#
{% set cleaned_file = "%s/features/%s.csv" | format(output_dir, dataset_params['name']) -%}
{% set rule_name = 'save_' ~ dataset_params['name'] | to_rule_name ~ '_final' -%}
{% do local_rules.append(rule_name) -%}
{% do training_set_features.append(cleaned_file | basename) %}
rule {{ rule_name }}:
    input: '{{ns.cur_output}}'
    output: '{{cleaned_file}}'
    run:
        df = pd.read_csv(input[0], index_col=0)
        df = df.rename(index={ind: '{{dataset_name}}_' + ind for ind in df.index})
        df.to_csv(output[0])

