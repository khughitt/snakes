    params:
        filter_params = {{ filter_params }},
        dataset_name = '{{ dataset_name }}'
    script:
        '{{ script_dir }}/filters/filter_gene_type.R' 
