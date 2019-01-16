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
{% set ns.cur_input  =  dat_cfg['path'] %}
{% set ns.cur_output =  '/'.join([output_dir, 'data', dat_cfg['name'], 'raw.csv']) %}

{# create a list of the columns that are used in the analysis -#}
{% set required_fields = [dat_cfg['sample_id'], dat_cfg['compound_id'], dat_cfg['response_var']] %}

{% for transform in dat_cfg['pipeline'] %}
{% if 'field' in transform %}
{% do required_fields.append(transform['field']) %}
{% endif %}
{% endfor %}

#
# Load raw curve data
#
{% set rule_name = 'read_' ~ dat_cfg['name'] | to_rule_name %}
{% do local_rules.append(rule_name) %}
rule {{ rule_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
    run:
        # for now, assume that all input files are provided in csv format with a
        # header and a column for row ids
        dat = pd.read_table(input[0], sep='{{ dat_cfg["sep"] }}', index_col={{ dat_cfg['index_col'] }})

        # create a list of the relevant fields to keep
        fields_to_keep = {{ required_fields | unique | list }}
        fields_to_keep = [x for x in fields_to_keep if x != dat.index.name]

        # drop unneeded fields and store result
        dat[fields_to_keep].to_csv(output[0])

{% if dat_cfg['pipeline'] | length > 0 %}
#
# Data transformations and filters
#
{% for transform in dat_cfg['pipeline'] %}
    {% set ns.cur_input  = ns.cur_output %}
    {% set ns.cur_output =  ns.cur_input | replace_filename(transform['name'] + '.csv') %}
    {% set rule_name = dat_cfg['name'] ~ "_" ~ transform['name'] | to_rule_name %}
    {% do local_rules.append(rule_name) %}
rule {{ rule_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
{% include 'pipeline/' + transform['type'] + '.snakefile' %}

{% endfor %}
{% endif %}

#
# Saved cleaned dataset
#
{% set cleaned_file = "%s/response/%s.csv" | format(output_dir, dat_cfg['name']) %}
{% set rule_name = 'save_' ~ dat_cfg['name'] | to_rule_name ~ '_final' %}
{% do local_rules.append(rule_name) %}
rule {{ rule_name }}:
    input: '{{ns.cur_output}}'
    output: '{{cleaned_file}}'
    run:
        df = pd.read_csv(input[0], index_col=0)
        #df = df.rename(index={ind: '{{dat_name}}_' + ind for ind in df.index})
        df.to_csv(output[0])

