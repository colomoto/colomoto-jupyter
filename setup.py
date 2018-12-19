# -*- coding: utf8 -*-

from setuptools import setup, find_packages

NAME = "colomoto_jupyter"

setup(name=NAME,
    version='0.5.3',
    author = "Loïc Paulevé",
    author_email = "loic.pauleve@ens-cachan.org",
    url = "https://github.com/colomoto/colomoto-jupyter",
    description = "CoLoMoTo helper functions for Juypter integration",
    long_description = """
Provides helper functions for integration in the CoLoMoTo Jupyter notebook.

See https://github.com/colomoto/colomoto-jupyter
""",
    install_requires = [
        "beautifulsoup4",
        "boolean.py",
    ],
    extras_require = {
        "networkx": ["networkx >= 2.0", "pydot", "pygraphviz"],
        "ipython": ["tabulate"],
    },
    license="LGPL v3+/CeCILL-C",
    include_package_data = True,
    packages = find_packages(),
    py_modules = ["cellcollective",
        "itstools", "itstools_setup",
        "nusmv", "nusmv_setup"],
    classifiers=[
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    keywords="jupyter, computational systems biology",
)

