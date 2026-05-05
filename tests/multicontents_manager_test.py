import os

import mock
import pytest
from tornado.web import HTTPError

from multicontents.multicontents_manager import MultiContentsManager
from multicontents.multicontents_manager import WrapperManager


class DummyManager(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __getattr__(self, name):
        self.__dict__[name] = mock.Mock()
        return self.__dict__[name]


class TestWrapperManager(object):
    @pytest.fixture
    def mock_import_module(self):
        with mock.patch("importlib.import_module") as m:
            m.return_value.DummyManager = DummyManager
            yield m

    @pytest.mark.parametrize("manager_cls", ["Dummy.DummyManager", DummyManager])
    def test_init(self, mock_import_module, manager_cls):
        wrapper = WrapperManager("", manager_cls, {"kwarg": "foo"})
        assert wrapper.proxy_path == ""
        assert isinstance(wrapper.manager, DummyManager)
        assert wrapper.manager.kwarg == "foo"

    @pytest.mark.parametrize(
        "proxy_path,path,expected_result",
        [
            ("", "foo", True),
            ("", "/foo", True),
            ("", "/foo/bar", True),
            ("", "foo/bar", True),
            ("foo", "/foo", True),
            ("foo", "/foo/bar", True),
            ("foo", "foo/bar", True),
            ("foo", "/foo/bar/baz", True),
            ("foo", "foo/bar/baz", True),
            ("foo", "bar", False),
        ],
    )
    def test_is_parent_directory_of(self, proxy_path, path, expected_result):
        manager = WrapperManager(proxy_path, DummyManager, {})
        assert manager.is_parent_directory_of(path) == expected_result

    @pytest.mark.parametrize(
        "proxy_path,path,expected_result",
        [
            ("", "foo", False),
            ("", "", False),
            ("foo", "/", True),
            ("foo", "foo", False),
            ("foo", "/foo", False),
            ("foo/bar", "foo/bar", False),
            ("foo/bar", "/foo/bar", False),
            ("foo/bar", "/foo", True),
            ("foo/bar", "foo", True),
        ],
    )
    def test_is_sub_directory_of(self, proxy_path, path, expected_result):
        manager = WrapperManager(proxy_path, DummyManager, {})
        assert manager.is_sub_directory_of(path) == expected_result

    @pytest.mark.parametrize(
        "proxy_path,path,expected_result",
        [
            ("", "/", ""),
            ("", "/foo", "foo"),
            ("foo", "/foo", ""),
            ("foo", "/foo/bar", "bar"),
            ("foo", "/foo/bar/baz", "bar/baz"),
            ("foo/bar", "/foo/bar/", ""),
            ("foo/bar", "/foo/bar/baz", "baz"),
        ],
    )
    def test_to_actual_path(self, proxy_path, path, expected_result):
        manager = WrapperManager(proxy_path, DummyManager, {})
        assert manager.to_actual_path(path) == expected_result

    @pytest.mark.parametrize(
        "proxy_path,path,expected_result",
        [
            ("", "", ""),
            ("", "foo", "foo"),
            ("foo", "", "foo"),
            ("foo", "bar/baz", "foo/bar/baz"),
            ("foo/bar", "baz", "foo/bar/baz"),
        ],
    )
    def test_to_proxy_path(self, proxy_path, path, expected_result):
        manager = WrapperManager(proxy_path, DummyManager, {})
        assert manager.to_proxy_path(path) == expected_result

    async def test_get(self):
        mock_get = mock.Mock(return_value={"content": [{"path": "foo/bar"}]})
        mock_dir_exists = mock.Mock(return_value=True)
        manager = WrapperManager(
            "proxy", DummyManager, {"get": mock_get, "dir_exists": mock_dir_exists}
        )
        with mock.patch.object(manager, "to_proxy_path") as mock_to_proxy:
            result = await manager.get("path")
        assert result["content"] == [{"path": mock_to_proxy()}]

    async def test_get_with_async_underlying_manager(self):
        async def async_get(path, *args, **kwargs):
            return {"content": [{"path": "foo/bar"}]}

        async def async_dir_exists(path):
            return True

        manager = WrapperManager(
            "proxy", DummyManager, {"get": async_get, "dir_exists": async_dir_exists}
        )
        result = await manager.get("proxy/somefile")
        assert result["content"] == [{"path": "proxy/foo/bar"}]

    @pytest.fixture
    def wrapper_maanger(self):
        manager = WrapperManager("proxy_path", DummyManager, {})
        with mock.patch.object(manager, "to_actual_path"):
            yield manager

    async def test_save(self, wrapper_maanger):
        await wrapper_maanger.save({}, "path")
        wrapper_maanger.manager.save.assert_called_once_with(
            {}, wrapper_maanger.to_actual_path.return_value
        )
        wrapper_maanger.to_actual_path.assert_called_once_with("path")

    async def test_delete_file(self, wrapper_maanger):
        await wrapper_maanger.delete_file("path")
        wrapper_maanger.manager.delete_file.assert_called_once_with(
            wrapper_maanger.to_actual_path.return_value
        )
        wrapper_maanger.to_actual_path.assert_called_once_with("path")

    async def test_file_exists(self, wrapper_maanger):
        await wrapper_maanger.file_exists("path")
        wrapper_maanger.manager.file_exists.assert_called_once_with(
            wrapper_maanger.to_actual_path.return_value
        )
        wrapper_maanger.to_actual_path.assert_called_once_with("path")

    async def test_dir_exists(self, wrapper_maanger):
        await wrapper_maanger.dir_exists("path")
        wrapper_maanger.manager.dir_exists.assert_called_once_with(
            wrapper_maanger.to_actual_path.return_value
        )
        wrapper_maanger.to_actual_path.assert_called_once_with("path")

    async def test_is_hidden(self, wrapper_maanger):
        await wrapper_maanger.is_hidden("path")
        wrapper_maanger.manager.is_hidden.assert_called_once_with(
            wrapper_maanger.to_actual_path.return_value
        )
        wrapper_maanger.to_actual_path.assert_called_once_with("path")

    async def test_rename_file(self, wrapper_maanger):
        wrapper_maanger.to_actual_path.side_effect = lambda path: f"patched-{path}"
        await wrapper_maanger.rename_file("old_path", "new_path")

        wrapper_maanger.manager.rename_file.assert_called_once_with(
            "patched-old_path", "patched-new_path"
        )
        wrapper_maanger.to_actual_path.assert_has_calls(
            [mock.call("old_path"), mock.call("new_path")]
        )


class TestMultiContentsManager(object):
    @pytest.fixture
    def manager_without_root(self):
        return MultiContentsManager(
            managers={
                "foo": {
                    "manager_class": DummyManager,
                    "kwargs": {"kwarg1": "value1", "kwarg2": "value2"},
                },
                "other": {
                    "manager_class": DummyManager,
                    "kwargs": {"kwarg3": "value3"},
                },
            }
        )

    @pytest.fixture
    def manager_with_root(self):
        return MultiContentsManager(
            managers={
                "": {
                    "manager_class": DummyManager,
                    "kwargs": {"kwarg1": "value1", "kwarg2": "value2"},
                },
                "child": {
                    "manager_class": DummyManager,
                    "kwargs": {"kwarg3": "value3"},
                },
            }
        )

    def test_init__with_root(self, manager_with_root):
        assert [m.proxy_path for m in manager_with_root._managers] == ["child", ""]

    def test_init__without_root(self, manager_without_root):
        assert [m.proxy_path for m in manager_without_root._managers] == [
            "other",
            "foo",
        ]

    @pytest.mark.parametrize(
        "path,expected_result",
        [("", ["abc", "def", "child"]), ("child", ["child/foo"])],
    )
    async def test_get_with_manager_with_root(
        self, manager_with_root, path, expected_result
    ):
        manager_with_root._managers[1].manager.dir_exists = mock.Mock(return_value=True)
        manager_with_root._managers[1].manager.get = mock.Mock(
            return_value={"content": [{"path": "abc"}, {"path": "def"}]}
        )
        manager_with_root._managers[0].manager.dir_exists = mock.Mock(return_value=True)
        manager_with_root._managers[0].manager.get = mock.Mock(
            return_value={"content": [{"path": "foo"}]}
        )
        result = await manager_with_root.get(path, content=True)
        assert [item["path"] for item in result["content"]] == expected_result

    @pytest.mark.parametrize(
        "path,expected_result",
        [
            ("/", ["other", "foo"]),
            ("foo", ["foo/abc", "foo/def"]),
            ("other", ["other/ghi"]),
        ],
    )
    async def test_get_without_manager_with_root(
        self, manager_without_root, path, expected_result
    ):
        manager_without_root._managers[1].manager.dir_exists = mock.Mock(
            return_value=True
        )
        manager_without_root._managers[1].manager.get = mock.Mock(
            return_value={"content": [{"path": "abc"}, {"path": "def"}]}
        )
        manager_without_root._managers[0].manager.dir_exists = mock.Mock(
            return_value=True
        )
        manager_without_root._managers[0].manager.get = mock.Mock(
            return_value={"content": [{"path": "ghi"}]}
        )
        result = await manager_without_root.get(path, content=True)
        assert [item["path"] for item in result["content"]] == expected_result

    async def test_rename_file_same_manager(self, manager_with_root):
        manager_with_root._managers[0].manager.rename_file = mock.Mock()
        await manager_with_root.rename_file("child/test1", "child/test2")
        manager_with_root._managers[0].manager.rename_file.assert_called_once_with(
            "test1", "test2"
        )

    @pytest.mark.parametrize(
        "old_path,new_path", [("/foo", "something/new"), ("something", "/foo")]
    )
    async def test_rename_file_virtual_direcotry(
        self, manager_without_root, old_path, new_path
    ):
        with pytest.raises(HTTPError):
            await manager_without_root.rename_file(old_path, new_path)

    async def test_rename_file_different_manager_file(self, manager_with_root):
        fake_model = {"path": "test1", "content": None, "type": "file"}
        manager_with_root._managers[0].manager.get = mock.Mock(return_value=fake_model)
        manager_with_root._managers[0].manager.dir_exists = mock.Mock(
            return_value=False
        )
        manager_with_root._managers[0].manager.delete_file = mock.Mock()
        manager_with_root._managers[1].manager.save = mock.Mock()

        async def fake_dir_exists(path):
            return False

        with mock.patch.object(
            manager_with_root, "dir_exists", side_effect=fake_dir_exists
        ):
            await manager_with_root.rename_file("child/test1", "test2")
        manager_with_root._managers[0].manager.get.assert_called_once_with("test1")
        manager_with_root._managers[1].manager.save.assert_called_once_with(
            fake_model, "test2"
        )
        manager_with_root._managers[0].manager.delete_file.assert_called_once_with(
            "test1"
        )

    def get_fake_item(self, path):
        items = {"folder_1": {"file_2": None, "folder_3": {"file_4": None}}}
        obj = items
        for key in path.strip("/").split("/"):
            obj = obj[key]
        return obj

    @pytest.fixture
    def mock_dir_exists(self, manager_with_root):
        async def dir_exists(path):
            return self.get_fake_item(path) is not None

        with mock.patch.object(manager_with_root, "dir_exists", side_effect=dir_exists):
            yield

    @pytest.fixture
    def mock_get(self, manager_with_root):
        async def get(path, **kwargs):
            obj = self.get_fake_item(path)
            content = (
                [{"name": key, "path": os.path.join(path, key)} for key in obj]
                if obj is not None
                else ""
            )
            return {"name": path.rsplit("/", 1)[-1], "path": path, "content": content}

        with mock.patch.object(manager_with_root, "get", side_effect=get):
            manager_with_root._managers[1].manager.dir_exists = mock.Mock(
                side_effect=lambda path: self.get_fake_item(path) is not None
            )
            manager_with_root._managers[1].manager.get = mock.Mock(
                side_effect=lambda path, **kwargs: {
                    "name": path.rsplit("/", 1)[-1],
                    "path": path,
                    "content": (
                        [{"name": key, "path": os.path.join(path, key)} for key in obj]
                        if (obj := self.get_fake_item(path)) is not None
                        else ""
                    ),
                }
            )
            yield

    async def test_rename_file_different_manager_dir(
        self, manager_with_root, mock_dir_exists, mock_get
    ):
        manager_with_root._managers[1].manager.delete_file = mock.Mock()
        manager_with_root._managers[0].manager.save = mock.Mock()

        await manager_with_root.rename_file("folder_1", "child/test_2")

        old_files = [
            "folder_1",
            "folder_1/file_2",
            "folder_1/folder_3",
            "folder_1/folder_3/file_4",
        ]
        manager_with_root._managers[1].manager.get.assert_has_calls(
            [mock.call(f) for f in old_files]
        )
        new_files = [
            "test_2",
            "test_2/file_2",
            "test_2/folder_3",
            "test_2/folder_3/file_4",
        ]
        manager_with_root._managers[0].manager.save.assert_has_calls(
            [mock.call(mock.ANY, f) for f in new_files]
        )
        manager_with_root._managers[1].manager.delete_file.assert_has_calls(
            [mock.call(f) for f in old_files], any_order=True
        )
