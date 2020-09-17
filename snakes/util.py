import os
import sys
import logging
import pandas as pd
from collections.abc import Mapping

def load_data(infile):
    """Attempts to detect filetype and load a specified dataset"""
    # check to make sure file exists
    if not os.path.exists(infile):
        logging.error(
            "Unable to find file: %s", infile
        )
        sys.exit()

    # load data
    if infile.endswith('.csv'):
        dat = pd.read_csv(infile)
    elif infile.endswith('.tsv'):
        dat = pd.read_csv(infile, sep='\t')
    elif infile.endswith('.feather'):
        dat = pd.read_feather(infile)
    elif infile.endswith('.parquet'):
        dat = pd.read_parquet(infile)

    return dat.set_index(dat.columns[0])

def recursive_update(d, u):
    """
    recursive dictionary update

    d: dict
        Dictionary to be updated
    u: dict
        Dictionary being applied

    source: https://stackoverflow.com/a/3233356/554531
    """
    for k, v in u.items():
        if isinstance(v, Mapping):
            d[k] = recursive_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d
