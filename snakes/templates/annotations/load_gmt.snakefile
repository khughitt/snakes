rule prepare_{{ gmt_name }}_{{ dataset_params['xid'] }}_gmt:
    input: '{{ gmt }}'
    output: '{{ preprocessed_gmt }}'
{% if dataset_params['xid'] == gene_set_params['gene_id'] %}
    shell: 'cp {{ gmt }} {{ preprocessed_gmt }}'
{% else %}    params:
        data_gid = '{{ dataset_params["xid"] }}',
        gset_gid = '{{ gene_set_params["gene_id"] }}'
    script: '{{ script_dir }}/annotations/prepare_gene_set.R'
{% endif %}
