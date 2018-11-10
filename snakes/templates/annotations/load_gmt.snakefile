rule prepare_{{ gmt_name }}_{{ dat_cfg['xid'] }}_gmt:
    input: '{{ gmt }}'
    output: '{{ preprocessed_gmt }}'
{% if dat_cfg['xid'] == gene_set_params['gene_id'] %}
    shell: 'cp {{ gmt }} {{ preprocessed_gmt }}'
{% else %}    params:
        data_gid = '{{ dat_cfg["xid"] }}',
        gset_gid = '{{ gene_set_params["gene_id"] }}'
    script: '{{ script_dir }}/annotations/prepare_gene_set.R'
{% endif %}

