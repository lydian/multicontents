import os
import time
import json

import pytest

from multicontents.multi_versions_file_checkpoints import MultiVersionsFileCheckpoints


class TestMultiVersionsFileCheckpoints(object):
    @pytest.fixture
    def root_dir(self, tmpdir):
        return str(tmpdir.mkdir("test"))

    @pytest.fixture
    def checkpoints(self, root_dir):
        return MultiVersionsFileCheckpoints(
            root_dir=root_dir, checkpoint_dir=".checkpoints"
        )

    def test_create_file_checkpoint(self, checkpoints):
        content = "test content"
        path = "inside/folder/file.txt"
        model = checkpoints.create_file_checkpoint(content, "text", path)

        generated_check_point = os.path.join(
            checkpoints.root_dir,
            ".checkpoints",
            "inside__folder__file___txt",
            model["id"],
        )

        with open(generated_check_point) as fp:
            generated_content = fp.read()
        assert content == generated_content

    def test_create_notebook_checkpoint(self, checkpoints):
        content = {}
        path = "inside/folder/file.ipynb"
        model = checkpoints.create_notebook_checkpoint(content, path)

        generated_check_point = os.path.join(
            checkpoints.root_dir,
            ".checkpoints",
            "inside__folder__file___ipynb",
            model["id"],
        )

        with open(generated_check_point) as fp:
            generated_content = fp.read()
        assert content == json.loads(generated_content)

    def test_list_checkpoints__no_checkpoint(self, checkpoints):
        assert checkpoints.list_checkpoints("not exists") == []

    def test_list_checkpoints_has_file_checkpoints(self, checkpoints):
        v1 = checkpoints.create_file_checkpoint("v1", "text", "file.txt")
        time.sleep(1)
        v2 = checkpoints.create_file_checkpoint("v2", "text", "file.txt")

        saved_checkpoints = checkpoints.list_checkpoints("file.txt")
        assert saved_checkpoints == [
            {"id": v2["id"], "last_modified": v2["last_modified"]},
            {"id": v1["id"], "last_modified": v1["last_modified"]},
        ]

    def test_list_checkpoints_has_nb_checkpoints(self, checkpoints):
        v1 = checkpoints.create_notebook_checkpoint({}, "notebook.ipynb")
        time.sleep(1)
        v2 = checkpoints.create_notebook_checkpoint({}, "notebook.ipynb")

        saved_checkpoints = checkpoints.list_checkpoints("notebook.ipynb")
        assert saved_checkpoints == [
            {"id": v2["id"], "last_modified": v2["last_modified"]},
            {"id": v1["id"], "last_modified": v1["last_modified"]},
        ]
