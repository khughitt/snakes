    params:
        args = {{ action }},
        dat_name = '{{ dat_name }}'
    script:
        '{{ script_dir }}/filters/filter_rows_gene_biotype_in.R' 


