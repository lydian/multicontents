# -*- coding: utf-8 -*-
import os
from IPython.html.services.contents.filemanager import FileContentsManager

from multicontents import MultiContentsManager


c = get_config()  # noqa
c.NotebookApp.nbserver_extensions = {"multicontents": True}

c.NotebookApp.contents_manager_class = MultiContentsManager
c.MultiContentsManager.managers = {
    "home": {
        "manager_class": FileContentsManager,
        "kwargs": {"root_dir": os.environ["HOME"]},
    },
    "tmp": {
        "manager_class": FileContentsManager,
        "kwargs": {"root_dir": os.environ.get("TEMP", "/tmp")},
    },
}

c.NotebookApp.token = ""
c.NotebookApp.password = ""
