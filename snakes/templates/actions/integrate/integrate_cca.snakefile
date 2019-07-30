    input: {{ action.inputs }}
    output: '{{ action.output }}'
    params: {{ action.params }}
    script:
        '{{ script_dir }}/integrate/integrate_cca.R' 
