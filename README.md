# Multicontents
[![Build Status](https://travis-ci.org/lydian/multicontents.svg?branch=master)](https://travis-ci.org/lydian/multicontents)
[![codecov](https://codecov.io/gh/lydian/multicontents/branch/master/graph/badge.svg)](https://codecov.io/gh/lydian/multicontents)

- Allow setting up multiple sources on jupyter
- Support moving data accross different sources

## Example
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

