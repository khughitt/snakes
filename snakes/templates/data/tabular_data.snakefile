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
{% set ns.cur_output =  '/'.join([output_dir, 'data', dataset.name, 'raw.csv']) %}
#
# Load {{ dataset.name }} data
#
{% set rule_name = 'load_' ~ dataset.name | to_rule_name %}
{% do local_rules.append(rule_name) %}
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
        {# ============== #}
        {# =   BRANCH   = #}
        {# ============== #}
        {% if action | is_list %}
            {# parent_output used to preserve last output filename prior to recursion. #}
            {% set parent_output = ns.cur_output %}
            {# iterate over branch actions #}
            {{- loop(action) }}
            {% set ns.cur_output = parent_output %}
        {# ==================== #}
        {# =   ACTION START   = #}
        {# ==================== #}
        {% else %}
            {# determine input and output filenames to use #}
            {# TODO: move logic to renderer?.. #}
            {% if action.file != '' %}
                {% set output_filename = action.file %}
            {% else %}
                {% set output_filename = action.action ~ '.csv' %}
            {% endif %}
            {% set ns.cur_input  = ns.cur_output %}
            {% set ns.cur_output =  ns.cur_input | replace_filename(output_filename) %}
rule {{ action.rule_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
            {% if not action.groupable %}
                {# ============================== #}
                {# =   ACTION (Non-groupable)   = #}
                {# ============================== #}
                {%- include 'actions/' + action.action | action_subdir + "/" + action.action + '.snakefile' %}
            {% else %}
    run:
        dat = pd.read_csv(input[0], index_col=0)
                {# ============== #}
                {# =   GROUP    = #}
                {# ============== #}
                {% if action.action == 'group' %}
                    {% for action in action.group_actions %}
                        {%- include 'actions/' + action.action | action_subdir + "/" + action.action + '.snakefile' %}
                    {% endfor %}
                {% else %}
                    {# ========================== #}
                    {# =   ACTION (Groupable)   = #}
                    {# ========================== #}
                    {%- include 'actions/' + action.action | action_subdir + "/" + action.action + '.snakefile' %}
                {% endif %}
        dat.to_csv(output[0])

            {% endif %}
        {% endif %}
        {# ==================== #}
        {# =   ACTION END   = #}
        {# ==================== #}
    {% endfor %}
{% endif %}

{# Keep track of last version of file processed #}
{% do terminal_datasets.append(ns.cur_output | basename_and_parent_dir) -%}
