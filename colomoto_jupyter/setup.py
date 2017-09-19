
from setuptools import setup, find_packages

NAME = "colomoto_jupyter"

setup(name=NAME,
    version='0.3.1',
    author = "Loïc Paulevé",
    author_email = "loic.pauleve@ens-cachan.org",
    url = "https://github.com/colomoto/colomoto-api",
    description = "CoLoMoTo helper functions for Juypter integration",
    long_description = """
Provides helper functions for integration in the CoLoMoTo Jupyter notebook.

See https://github.com/colomoto/colomoto-api
""",
    extras_require = {
        "networkx": ["networkx", "pydotplus", "pygraphviz"],
    },
    license="LGPL v3+/CeCILL-C",
    include_package_data = True,
    packages = find_packages(),
    classifiers=[
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    keywords="jupyter, computational systems biology",
)

