    input: '{{ action.input }}'
    output: '{{ action.output }}'
    params:
        args = {{ action.params }}
    script:
        '{{ script_dir }}/filter/filter_rows_max_correlation.R' 


