import os
import re
import datetime
import importlib

from notebook.services.contents.manager import ContentsManager
from tornado.web import HTTPError
from traitlets import Dict

from multicontents.no_op_checkpoints import NoOpCheckpoints

DUMMY_CREATED_DATE = datetime.datetime.fromtimestamp(86400)


def build_base_model(
    type_,
    path,
    writable=True,
    last_modified=None,
    created=None,
    content=None,
    format=None,
    mimetype=None,
):
    return {
        "name": path.rstrip("/").rsplit("/", 1)[-1],
        "path": path,
        "writable": writable,
        "last_modified": last_modified or DUMMY_CREATED_DATE,
        "created": created or DUMMY_CREATED_DATE,
        "content": content,
        "mimetype": mimetype,
        "format": format,
        "type": type_,
    }


class WrapperManager(object):
    def __init__(self, proxy_path, manager_class, manager_kwargs):
        self.proxy_path = proxy_path
        if isinstance(manager_class, str):
            module_name, cls_name = manager_class.rsplit(".", 1)
            manager_class = getattr(importlib.import_module(module_name), cls_name)
        self.manager = manager_class(**manager_kwargs)

    def is_parent_directory_of(self, path):
        path = path.strip("/")
        proxy_folders = self.proxy_path.split("/") if self.proxy_path != "" else []
        path_folders = path.lstrip("/").split("/")
        return len(path_folders) >= len(proxy_folders) and "/".join(
            proxy_folders
        ) == "/".join(path_folders[: len(proxy_folders)])

    def is_sub_directory_of(self, path):
        path = path.strip("/")
        proxy_parent = ("/" + self.proxy_path).rsplit("/", 1)[0]
        return (
            proxy_parent.lstrip("/") == path.lstrip("/")
            and path.lstrip("/") != self.proxy_path
        )

    def to_actual_path(self, path):
        path = path.strip("/")
        if re.match(f"^{re.escape(self.proxy_path)}$", path):
            return ""
        return re.sub(f"^{re.escape(self.proxy_path)}/", r"/", path).strip("/")

    def to_proxy_path(self, actual_path):
        actual_path = actual_path.strip("/")
        return os.path.join(self.proxy_path, actual_path).strip("/")

    def get(self, path, *args, **kwargs):
        result = self.manager.get(self.to_actual_path(path), *args, **kwargs)
        if result.get("content", None) and self.dir_exists(path):
            result["content"] = [
                dict(
                    list(model.items()) + [("path", self.to_proxy_path(model["path"]))]
                )
                for model in result["content"]
            ]
        return result

    def save(self, model, path):
        return self.manager.save(model, self.to_actual_path(path))

    def delete_file(self, path):
        return self.manager.delete_file(self.to_actual_path(path))

    def file_exists(self, path=None):
        return self.manager.file_exists(self.to_actual_path(path))

    def dir_exists(self, path):
        return self.manager.dir_exists(self.to_actual_path(path))

    def is_hidden(self, path):
        return self.manager.is_hidden(self.to_actual_path(path))

    def rename_file(self, old_path, new_path):
        self.manager.rename_file(
            self.to_actual_path(old_path), self.to_actual_path(new_path)
        )


class MultiContentsManager(ContentsManager):

    managers = Dict(help="the path to manager_class settings").tag(config=True)

    def __init__(self, *args, **kwargs):
        super(MultiContentsManager, self).__init__(*args, **kwargs)
        self._managers = [
            WrapperManager(path.lstrip("/"), config["manager_class"], config["kwargs"])
            for path, config in self.managers.items()
        ]
        # path are searched based on the depth, so that we will always match
        # to the closest one first
        self._managers.sort(
            key=lambda manager: (
                manager.proxy_path == "",  # non root matched first
                -len(manager.proxy_path.split("/")),  # match deeper folder first
                -len(
                    manager.proxy_path.rsplit("/", 1)[-1]
                ),  # match longest directory name first
            )
        )

    def get_manager(self, path):
        for manager in self._managers:
            if manager.is_parent_directory_of(path):
                return manager
        raise HTTPError(404, f"Manager not found for path: '{path}'")

    def get(self, path, *args, **kwargs):
        try:
            manager = self.get_manager(path)
            current = manager.get(path, *args, **kwargs)
            is_dir = manager.dir_exists(path)
        except HTTPError as e:
            # if root is not configured, we build a virtual directory to list all
            # the defined path
            if path == "/":
                current = build_base_model(
                    type_="directory",
                    path="/",
                    format="json",
                    content=[] if kwargs.get("content", None) else None,
                )
                is_dir = True
            else:
                raise e

        # add virtual directory
        if kwargs.get("content", None) and is_dir:
            extra = [
                build_base_model(
                    type_="directory", path=other_manager.to_proxy_path("")
                )
                for other_manager in self._managers
                if other_manager.is_sub_directory_of(path)
            ]
            current["content"] += extra
        return current

    def rename_file(self, old_path, new_path):
        old_manager = self.get_manager(old_path)
        new_manager = self.get_manager(new_path)

        if old_manager == new_manager:
            old_manager.rename_file(old_path, new_path)
        else:
            model = old_manager.get(old_path)
            new_manager.save(model, new_path)
            old_manager.delete_file(old_path)

    def save(self, model, path):
        return self.get_manager(path).save(model, path)

    def delete_file(self, path):
        return self.get_manager(path).delete_file(path)

    def file_exists(self, path=None):
        return self.get_manager(path).file_exists(path)

    def dir_exists(self, path):
        return self.get_manager(path).dir_exists(path)

    def is_hidden(self, path):
        return self.get_manager(path).is_hidden(path)

    def _checkpoints_class_default(self):
        return NoOpCheckpoints
