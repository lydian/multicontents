import os
import datetime

from jupyter_core.utils import ensure_dir_exists


try:
    from jupyter_server.services.contents.filecheckpoints import GenericFileCheckpoints
except ImportError:
    from notebook.services.contents.filecheckpoints import GenericFileCheckpoints


class MultiVersionsFileCheckpoints(GenericFileCheckpoints):
    def checkpoint_path(self, checkpoint_id, path):
        """find the path to a checkpoint"""
        checkpoint_dir = self.get_checkpoints_path_for_file(path)
        with self.perm_to_403():
            ensure_dir_exists(checkpoint_dir)
        cp_path = os.path.join(checkpoint_dir, checkpoint_id)
        return cp_path

    def get_checkpoints_path_for_file(self, path, create_missing=False):
        path = path.strip("/")
        checkpoint_dir = os.path.join(
            self.root_dir,
            self.checkpoint_dir,
            path.replace("/", "__").replace(".", "___"),
        )
        if create_missing and not os.path.isdir(checkpoint_dir):
            os.makedirs(checkpoint_dir, exist_ok=True)
        return checkpoint_dir

    def get_checkpoint_dir_and_id(self, path, create_missing=False):
        checkpoint_dir = self.get_checkpoints_path_for_file(
            path, create_missing=create_missing
        )
        saved_time = datetime.datetime.now(datetime.timezone.utc)
        checkpoint_id = str(saved_time.timestamp()).replace(".", "")
        return checkpoint_dir, checkpoint_id

    def create_file_checkpoint(self, content, format, path):
        checkpoint_dir, checkpoint_id = self.get_checkpoint_dir_and_id(
            path, create_missing=True
        )
        checkpoint_file_path = os.path.join(checkpoint_dir, checkpoint_id)
        self.log.debug("creating checkpoint for %s", path)
        with self.perm_to_403():
            self._save_file(checkpoint_file_path, content, format=format)
        return self.checkpoint_model(checkpoint_id, checkpoint_file_path)

    def create_notebook_checkpoint(self, nb, path):
        checkpoint_dir, checkpoint_id = self.get_checkpoint_dir_and_id(
            path, create_missing=True
        )
        checkpoint_file_path = os.path.join(checkpoint_dir, checkpoint_id)
        self.log.debug("creating checkpoint for %s", path)
        with self.perm_to_403():
            self._save_notebook(checkpoint_file_path, nb)
        return self.checkpoint_model(checkpoint_id, checkpoint_file_path)

    def list_checkpoints(self, path):
        checkpoint_dir = self.get_checkpoints_path_for_file(path)
        if not os.path.isdir(checkpoint_dir):
            return []
        checkpoints = [
            self.checkpoint_model(
                file_name,
                os.path.join(self.get_checkpoints_path_for_file(path), file_name),
            )
            for file_name in os.listdir(checkpoint_dir)
        ]
        return sorted(checkpoints, key=lambda c: -c["last_modified"].timestamp())
