    params:
        args = {{ action }},
        dat_name = '{{ dat_name }}'
    script:
        '{{ script_dir }}/filters/filter_gene_type.R' 


