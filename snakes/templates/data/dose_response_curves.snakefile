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
{% set required_fields = [dat_cfg['sample_id'], dat_cfg['compound_id']] -%}

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

