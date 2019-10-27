# -*- coding: utf-8 -*-
import os

from setuptools import find_packages
from setuptools import setup


with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.md")) as fp:
    long_description = fp.read()

setup(
    name="multicontents",
    version="0.1.0",
    description="providing contents from multiple sources in jupyter notebook",
    long_description_content_type="text/markdown",
    long_description=long_description,
    url="https://github.com/lydian/multicontents",
    author="Lydian Lee",
    author_email="lydianly@gmail.com",
    maintainer="Lydian Lee",
    maintainer_email="lydianly@gmail.com",
    packages=find_packages(),
    install_requires=["notebook", "ipykernel"],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)
