        dat.columns = [x.replace("{{ action.params['old'] }}", "{{ action.params['new'] }}") for x in dat.columns]

