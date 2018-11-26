rule prepare_{{ gene_set_name | to_rule_name }}_{{ dat_cfg['xid'] | to_rule_name }}_gmt:
    input: '{{ gmt }}'
    output: '{{ preprocessed_gmt }}'
{% if dat_cfg['xid'] == gene_set_params['gene_id'] %}
    shell: 'cp {{ gmt }} {{ preprocessed_gmt }}'
{% else %}    params:
        data_gid = '{{ dat_cfg["xid"] }}',
        gset_gid = '{{ gene_set_params["gene_id"] }}'
    script: '{{ script_dir }}/annotations/prepare_gene_set.R'
{% endif %}

