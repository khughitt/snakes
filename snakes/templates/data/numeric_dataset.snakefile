################################################################################
#
# {% block header_comment %}
# Generic Numeric Dataset workflow
# {% endblock %}
#
################################################################################
{# variables to keep track of rule inputs and outputs -#}
{% set cur_input  =  feature['path'] -%}
{% set cur_output =  config['output_dir'] + '/raw/' + feature['name'] + '.csv' -%}
rule {% block start_rule %}{% endblock %}:
    input: '{{ cur_input }}'
    output: '{{ cur_output }}'
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

{% if 'filter' in feature and 'early' in feature['filter'] -%}
{% for filter_name, filter_params in feature['filter']['early'].items() -%}
rule {{ feature['name'] }}_filter_early_{{ filter_name }}:
    # foo
{% endfor -%}
{% endif -%}

{#
# vim: ft=python
#}
