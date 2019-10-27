from notebook.services.contents.filecheckpoints import GenericFileCheckpoints


class NoOpCheckpoints(GenericFileCheckpoints):
    """requires the following methods:"""

    def delete_checkpoint(self, checkpoint_id, path):
        """deletes a checkpoint for a file"""
        pass

    def list_checkpoints(self, path):
        """returns a list of checkpoint models for a given file,
        default just does one per file
        """
        return []
