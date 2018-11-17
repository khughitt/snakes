################################################################################
#
# {% block header_comment %}
# Generic Dose Response Curve Data
# {% endblock %}
#
################################################################################
{############################################################################################-#}
{# Below we define a custom namespace which is used to keep track of the most recent rule
{# included for the dataset. The namespace approach is required so that variables can be
{# modified in the scope of a jinja for loop.
{############################################################################################-#}
{% set ns = namespace(found=false) %}
{% set ns.cur_input  =  dat_cfg['path'] -%}
{% set ns.cur_output =  '/'.join([output_dir, 'data', dat_cfg['name'], 'raw.csv']) -%}

{# create a list of the columns that are used in the analysis -#}
{% set required_fields = [dat_cfg['sample_id'], dat_cfg['compound_id'], dat_cfg['response_var']] -%}

{% for filter_name, filter_params in dat_cfg['filters'].items() -%}
{% if 'field' in filter_params -%}
{% do required_fields.append(filter_params['field']) -%}
{% endif -%}
{% endfor -%}

#
# Load raw curve data
#
{% set rule_name = 'read_' ~ dat_cfg['name'] | to_rule_name -%}
{% do local_rules.append(rule_name) -%}
rule {{ rule_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
    run:
        # create a list of the relevant fields to keep
        fields_to_keep = {{ required_fields | unique | list }}

        # for now, assume that all input files are provided in csv format with a
        # header and a column for row ids
        pd.read_csv(input[0])[fields_to_keep].to_csv(output[0])

{% if 'filters' in dat_cfg -%}
#
# Data filtering
#
{% for filter_name, filter_params in dat_cfg['filters'].items() -%}
    {% set ns.cur_input  = ns.cur_output -%}
    {% set ns.cur_output =  ns.cur_input | replace_filename('filter_' + filter_name + '.csv') -%}
{% set rule_name = dat_cfg['name'] ~ '_filter_' ~ filter_name | to_rule_name -%}
{% do local_rules.append(rule_name) -%}
rule {{ rule_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
{% include 'filters/' + filter_params['type'] + '.snakefile' %}
{% endfor %}
{% endif -%}

{% if 'transforms' in dat_cfg -%}
#
# Data transformations
#
{% for transform in dat_cfg['transforms'] -%}
    {% set ns.cur_input  = ns.cur_output -%}
    {% set ns.cur_output =  ns.cur_input | replace_filename('transform_' + transform + '.csv') -%}
{% set rule_name = dat_cfg['name'] ~ '_' ~ transform ~ '_transform' | to_rule_name -%}
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
{% set cleaned_file = "%s/response/%s.csv" | format(output_dir, dat_cfg['name']) -%}
{% set rule_name = 'save_' ~ dat_cfg['name'] | to_rule_name ~ '_final' -%}
{% do local_rules.append(rule_name) -%}
rule {{ rule_name }}:
    input: '{{ns.cur_output}}'
    output: '{{cleaned_file}}'
    run:
        df = pd.read_csv(input[0], index_col=0)
        #df = df.rename(index={ind: '{{dat_name}}_' + ind for ind in df.index})
        df.to_csv(output[0])

