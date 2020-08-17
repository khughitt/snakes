    input: '{{ action.input }}'
    output: '{{ action.output }}'
    params:
        key_type = '{{ dataset.xid }}',
        gene_biotypes = {{ action.params['gene_biotypes'] }}
    script:
        '{{ script_dir }}/filter/filter_rows_gene_biotype_in.R' 


