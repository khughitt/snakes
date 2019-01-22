    params:
        args = {{ action }},
        dat_name = '{{ dat_name }}'
    script:
        '{{ script_dir }}/pipeline/impute_knn.R' 


