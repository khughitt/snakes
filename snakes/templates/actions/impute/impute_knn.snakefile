    input: '{{ action.input }}'
    output: '{{ action.output }}'
    params:
        args = {{ action.params }}
    script:
        '{{ script_dir }}/impute/impute_knn.R' 


