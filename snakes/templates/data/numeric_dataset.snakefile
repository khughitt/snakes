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
{% set ns.cur_input  =  dataset['path'] -%}
{% set ns.cur_output =  config['output_dir'] + '/' + dataset['name'] + '/raw.csv' -%}
#
# Load raw data from one or more files
#
# Input must either be a valid filepath to a tab-delimited data matrix, or a wildcard (glob)
# expression pointing to multiple plain-text files, each containing a single column.
#
rule read_{{ dataset['name'] }}:
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

        dat.to_csv(str(output[0]), sep='\t', index_label='{{ dataset["xid"] }}')

{% if 'filter' in dataset -%}
#
# Data filtering
#
{% for filter_name, filter_params in dataset['filter'].items() -%}
    {% set ns.cur_input  = ns.cur_output -%}
    {% set ns.cur_output =  config['output_dir'] + '/' + dataset['name'] + '/filter_' + filter_name + '.csv' -%}
rule {{ dataset['name'] }}_filter_{{ filter_name }}:
    input: '{{ ns.cur_input }}'
    output: '{{ ns.cur_output }}'
    {% include 'filters/' + filter_params['type'] + '.snakefile' %}
{% endfor -%}
{% endif -%}

#
# Saved cleaned dataset
#
{% set cleaned_file = config['output_dir'] + '/' + dataset['name'] + '/cleaned.csv' -%}
rule {{ dataset['name'] }}_cleaned:
    input: '{{ns.cur_output}}'
    output: '{{cleaned_file}}'
    shell: 'cp {input} {output}'

{# update dict with most recent rule in workflow -#}
{% do most_recent_rules.update({dataset['name']: cleaned_file}) %}

