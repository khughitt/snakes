################################################################################
#
# {% block header_comment %}
# Abstract gene set template 
# {% endblock %}
#
################################################################################
#
# Aggregates gene features into pre-defined gene sets and applies one more functions to derrive
# new features.
#
{% for gmt in gene_set_params['gmts'] %}
{% set gmt_name = gmt | basename_no_ext -%}
{% set output_path = "%s/%s/gene-sets/%s-%s-{fxns}.csv" | format(config['output_dir'], dataset_name, gene_set, gmt_name) -%}

rule gene_set_{{dataset_name}}_{{ gene_set }}_{{ gmt_name }}:
    input: '{{ cur_input }}'
    output: expand("{{ output_path }}", fxns = {{ gene_set_params['fxns'] }})
    params:
        gmt: '{{ gmt }}'
    run:
        # todo

{% endfor -%}

