import os

from jupyter_server.services.contents.filemanager import FileContentsManager
from s3contents import S3ContentsManager

from multicontents import MultiContentsManager

c = get_config()  # noqa: F821

c.ServerApp.contents_manager_class = MultiContentsManager
c.MultiContentsManager.managers = {
    "local": {
        "manager_class": FileContentsManager,
        "kwargs": {"root_dir": os.environ["LOCAL_ROOT"]},
    },
    "s3": {
        "manager_class": S3ContentsManager,
        "kwargs": {
            "bucket": os.environ["S3_BUCKET"],
            "access_key_id": "test",
            "secret_access_key": "test",
            "endpoint_url": os.environ["MOTO_ENDPOINT"],
        },
    },
}

c.AsyncMultiVersionsFileCheckpoints.root_dir = os.environ["LOCAL_ROOT"]

c.ServerApp.token = ""
c.ServerApp.password = ""
c.ServerApp.disable_check_xsrf = True
