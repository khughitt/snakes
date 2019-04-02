# Snakes Action Templates

This directory contains the template logic for all supported Snakes actions (filters, transforms,
etc.)

### Creating new actions

To add support for a new transform:

1. Create a `.snakefile`  with the appropriate name, and add the functionality logic to it, using
   the [jinja2](http://jinja.pocoo.org/docs/2.10/)  `{{ variable }}` syntax in places where
   variables are to be filled.
2. Edit `snakes/conf/defaults.yml` and `snakes/conf/required.yml` to specify any default / required
   function parameters.
3. If you plan to submit the new functionality back to the main project, also be sure to update the
   documentation, and consider including relevant unit tests for the new functionality.

**Note**: Due to the way individual templates are assembled into the final Snakefile, it is
important to leave two spaces at the bottom of each action template. Otherwise the rules will
not appear correctly in the final Snakefile.
