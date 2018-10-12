################################################################################
#
# {% block header_comment %}
# Generic Numeric Dataset workflow
# {% endblock %}
#
################################################################################
{##############################################-#}
{# Variables to keep track of most recent rule -#}
{# names. "namespace" used to allow scope to   -#}
{# modified from within loops.                 -#}
{##############################################-#}
{% set ns = namespace(found=false) %}
{% set ns.cur_input  =  feature['path'] -%}
{% set ns.cur_output =  config['output_dir'] + '/' + feature['name'] + '/raw.csv' -%}
#
# Load raw data
#
rule {% block start_rule %}{% endblock %}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
    run:
        # get path to input file(s)
        input_files = glob.glob(input)

        # if only one file, read in as-is
        if len(input_files) == 1:
            dat = pd.read_table(input_files[0])
        else:
            # otherwise, assume one file per sample and combine into a single dataset
            cols = []
            names = []

            for input_file in input_files:
                # cols.append(pd.read_table(input_file).ix[:, data_col])
                cols.append(pd.read_table(input_file))

                # use filename without extension as sample id
                # names.append(sample_from_filename_func(input_file))
                names.append(os.path.splitext(os.path.basename(x))[0])

            dat = pd.concat(cols, axis=1)
            dat.columns = names

        dat.to_csv(str(output[0]), sep='\t', index_label='{{ feature["xid"] }}')

{% if 'filter' in feature -%}
#
# Data filtering
#
{% for filter_name, filter_params in feature['filter'].items() -%}
    {% set ns.cur_input  = ns.cur_output -%}
    {% set ns.cur_output =  config['output_dir'] + '/' + feature['name'] + '/filter_' + filter_name + '.csv' -%}
rule {{ feature['name'] }}_filter_{{ filter_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
    {% include 'filters/' + filter_params['type'] + '.snakefile' %}
{% endfor -%}
{% endif -%}
{# update dict with most recent rule in workflow -#}
{% do most_recent_rules.update({feature['name']: ns.cur_output}) %}
{#
# vim: ft=python
-#}
