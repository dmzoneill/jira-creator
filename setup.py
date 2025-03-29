# -*- coding: utf-8 -*-
from setuptools import setup

packages = ["jira_creator"]

package_data = {"": ["*", "jira_creator/*"]}

install_requires = ["requests"]

entry_points = {
    "console_scripts": [
        "jira-creator = jira_creator.jiracreator:app",
    ]
}

setup_kwargs = {
    "name": "jira-creator",
    "version": "0.0.13",
    "description": "Jira console app",
    "long_description": "",
    "author": "David O Neill",
    "author_email": "dmz.oneill@gmail.com",
    "maintainer": None,
    "maintainer_email": None,
    "url": "https://github.com/dmzoneill/jira-creator",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "entry_points": entry_points,
    "include_package_data": True,
    "python_requires": ">=3.11,<4.0",
}


setup(**setup_kwargs)
