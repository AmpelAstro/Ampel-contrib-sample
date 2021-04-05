#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : setup.py
# License           : BSD-3-Clause
# Author            : jvs
# Date              : Unspecified
# Last Modified Date: 04.04.2021
# Last Modified By  : jno 

from setuptools import find_namespace_packages, setup

setup(
    name="ampel-contrib-sample",
    version="0.7.1-alpha.0",
    packages=find_namespace_packages(),
    package_data={
        "": ["*.json", "py.typed"],  # include any package containing *.json files
        "conf": [
            "*.json",
            "**/*.json",
            "**/**/*.json",
            "*.yaml",
            "**/*.yaml",
            "**/**/*.yaml",
            "*.yml",
            "**/*.yml",
            "**/**/*.yml",
        ],
    },
    install_requires=[
        'ampel-interface>=0.7.1-alpha.7,<0.7.2',
        'ampel-core[plotting]>=0.7.1-alpha.3,<0.7.2',
        'ampel-photometry>=0.7.1-alpha.0,<0.7.2',
        'ampel-alerts>=0.7.1-alpha.0,<0.7.2',
        'ampel-ztf>=0.7.1-alpha.8,<0.7.2',
#        "catsHTM",
        "extcats",
        "zerorpc",
        # see: https://github.com/sncosmo/sncosmo/issues/291 - should be fixed now
        "sncosmo==2.2.0",
        "iminuit==1.5.1",
#        "sncosmo",
#        "iminuit",
        "sfdmap",
        "astropy",
        "numpy",
        "scipy",
#        "beautifulsoup4",
#       "backoff",
#        "requests",
#        "pymage @ https://github.com/MickaelRigault/pymage/archive/v1.0.tar.gz",
        # pymage secretly depends on pandas
#        "pandas",
    ],
)
