"""
Snakes Fixture

Note: When running tests in a virtualenv container, be sure to install py.test
      in the virtualenv so that system version isn't used instead.
"""
import os
import pytest
import time
from snakes import SnakefileRenderer

@pytest.fixture(scope="session")
def renderer(tmpdir_factory):
    conf = 'tests/settings/config.yml'
    outfile = str(tmpdir_factory.mktemp('output').join('Snakefile'))

    return SnakefileRenderer(conf, output_file=outfile)
