# Multicontents
[![Build Status](https://travis-ci.org/lydian/multicontents.svg?branch=master)](https://travis-ci.org/lydian/multicontents)
[![codecov](https://codecov.io/gh/lydian/multicontents/branch/master/graph/badge.svg)](https://codecov.io/gh/lydian/multicontents)

It's intentionally to do things like HybridContentsManager (from pgcontents) which allow setting up multiple sources on jupyter.
With extra features including:
- Support moving data accross different sources
- The package is pretty lightweight, which means you don't need to install extra library if you only want the multi backend support.


## Install
1. install multicontents
```
pip install multicontents
```
2. configure jupyter_notebook_config.py
```
from multicontents import MultiContentsManager
from IPython.html.services.contents.filemanager import FileContentsManager
from s3contents import S3ContentsManager

c.NotebookApp.contents_manager_class = MultiContentsManager
c.MultiContentsManager.managers = {
    "home": {
        "manager_class": FileContentsManager,
        "kwargs": {
            "root_dir": os.environ["HOME"]
        },
    },
    "s3": {
        "manager_class": S3ContentsManager,
        "kwargs": {
            "bucket": "example-bucket",
            "prefix": "path/to/notebooks",
        },
    },
}
```

## Develoop
1. clone the repo:
```git clone git@github.com:lydian/multicontents.git```
2. run testing with ```make server```
3. You can modify example config file for testing

I'll try my best to do CR pull request!


