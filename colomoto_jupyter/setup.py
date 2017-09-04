
from setuptools import setup, find_packages

NAME = "colomoto_jupyter"

setup(name=NAME,
    author = "Loïc Paulevé",
    author_email = "loic.pauleve@ens-cachan.org",
    url = "https://github.com/colomoto/colomoto-api",
    version='0.1',
    description = "CoLoMoTo helper functions for Juypter integration",
    long_description = open("README.rst").read(),
    install_requires = [
        "networkx",
        "pydotplus",
        "pygraphviz",
    ],
    packages = find_packages(),
)

