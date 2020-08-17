#
# PLACEHOLDER (To be implemented at a future date...)
#
# Possible approach:
#
#   1. Update all filter functions to accept an option "mask" argument to have func return a
#      boolean mask, instead of applying filter directly to data
#   2. Create filter_and, etc. functions which accept two filter names and dicts of arguments,
#      which then calls each filter function with `mask=True`, and then applies binary operation
#      to resulting masks.
#   3. Combined mask is then applied to data and results are returned.
#   4. As an alternative to `mask=True` approach, each filters.filter_xx function could be split
#      into two funcs: one mask_xx and one filter_xx (the later of which calls the former..)
#
# Alternative approach:
#
# Create a matching mask_xx template for each filter_xx function, which only handles the mask
# generation.  Single filter functions would then contain a 'run:' directive, {% include mask_xx
# %}, and then then applies the mask to the data.
#
# This could potentially be simplified by only having a few filter_xx templates (one for single 
# filters, and one for each binary filter..), all of which use {% import %} to import the
# appropriate mask templates.
#
# E.g.
#
# filter.snakefile
# filter_and.snakefile
# filter_or.snakefile
# mask_rows_xx
# mask_rows_yy
# etc.
#
# For this approach, the data templates would need to be modified to mofified accordingly, as well.
#
    run:
        dat = pd.read_feather(input[0])
        dat = dat.set_index(dat.columns[0])

        dat = filters.filter_and('{{ action.params['filter1'] }}', 
                                 '{{ action.params['filter2'] }}', 
                                 fargs1={{ action.params['fargs1'] }}, 
                                 fargs2={{ action.params['fargs2'] }})

        dat.reset_index().to_feather(output[0], compression='lz4')


