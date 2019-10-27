# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

from setuptools import find_packages
from setuptools import setup


with open("README.md") as fp:
    long_description = fp.read()

setup(
    name="multicontents",
    version="0.1.0",
    description="providing contents from multiple sources in jupyter notebook",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lydian/multicontents",
    author="Lydian Lee",
    author_email="lydianly@gmail.com",
    maintainer="Lydian Lee",
    maintainer_email="lydianly@gmail.com",
    packages=find_packages(exclude=("tests*",)),
    install_requires=["notebook", "ipykernel"],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)
