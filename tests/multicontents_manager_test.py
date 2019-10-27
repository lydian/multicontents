import mock
import pytest

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

    def test_get(self):
        mock_get = mock.Mock(return_value={"content": [{"path": "foo/bar"}]})
        mock_dir_exists = mock.Mock(return_value=True)
        manager = WrapperManager(
            "proxy", DummyManager, {"get": mock_get, "dir_exists": mock_dir_exists}
        )
        with mock.patch.object(manager, "to_proxy_path") as mock_to_proxy:
            result = manager.get("path")
        assert result["content"] == [{"path": mock_to_proxy()}]

    @pytest.fixture
    def wrapper_maanger(self):
        manager = WrapperManager("proxy_path", DummyManager, {})
        with mock.patch.object(manager, "to_actual_path"):
            yield manager

    def test_save(self, wrapper_maanger):
        wrapper_maanger.save({}, "path")
        wrapper_maanger.manager.save.assert_called_once_with(
            {}, wrapper_maanger.to_actual_path.return_value
        )
        wrapper_maanger.to_actual_path.assert_called_once_with("path")

    def test_delete_file(self, wrapper_maanger):
        wrapper_maanger.delete_file("path")
        wrapper_maanger.manager.delete_file.assert_called_once_with(
            wrapper_maanger.to_actual_path.return_value
        )
        wrapper_maanger.to_actual_path.assert_called_once_with("path")

    def test_file_exists(self, wrapper_maanger):
        wrapper_maanger.file_exists("path")
        wrapper_maanger.manager.file_exists.assert_called_once_with(
            wrapper_maanger.to_actual_path.return_value
        )
        wrapper_maanger.to_actual_path.assert_called_once_with("path")

    def test_dir_exists(self, wrapper_maanger):
        wrapper_maanger.dir_exists("path")
        wrapper_maanger.manager.dir_exists.assert_called_once_with(
            wrapper_maanger.to_actual_path.return_value
        )
        wrapper_maanger.to_actual_path.assert_called_once_with("path")

    def test_rename_file(self, wrapper_maanger):
        wrapper_maanger.to_actual_path.side_effect = lambda path: f"patched-{path}"
        wrapper_maanger.rename_file("old_path", "new_path")

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
        "path,expected_result", [("", ["abc", "def", "child"]), ("child", ["foo"])]
    )
    def test_get_with_manager_with_root(self, manager_with_root, path, expected_result):
        manager_with_root._managers[1].dir_exists = mock.Mock(return_value=True)
        manager_with_root._managers[1].get = mock.Mock(
            return_value={"content": [{"path": "abc"}, {"path": "def"}]}
        )
        manager_with_root._managers[0].get = mock.Mock(
            return_value={"content": [{"path": "foo"}]}
        )
        result = manager_with_root.get(path, content=True)
        assert [item["path"] for item in result["content"]] == expected_result

    @pytest.mark.parametrize(
        "path,expected_result",
        [("/", ["other", "foo"]), ("foo", ["abc", "def"]), ("other", ["ghi"])],
    )
    def test_get_without_manager_with_root(
        self, manager_without_root, path, expected_result
    ):
        manager_without_root._managers[1].get = mock.Mock(
            return_value={"content": [{"path": "abc"}, {"path": "def"}]}
        )
        manager_without_root._managers[0].get = mock.Mock(
            return_value={"content": [{"path": "ghi"}]}
        )
        result = manager_without_root.get(path, content=True)
        assert [item["path"] for item in result["content"]] == expected_result

    def test_rename_file_same_manager(self, manager_with_root):
        manager_with_root._managers[0].rename_file = mock.Mock()
        manager_with_root.rename_file("child/test1", "child/test2")
        manager_with_root._managers[0].rename_file.assert_called_once_with(
            "child/test1", "child/test2"
        )

    def test_rename_file_different_manager(self, manager_with_root):
        manager_with_root._managers[0].get = mock.Mock()
        manager_with_root._managers[0].delete_file = mock.Mock()
        manager_with_root._managers[1].save = mock.Mock()
        manager_with_root.rename_file("child/test1", "test2")
        manager_with_root._managers[0].get.assert_called_once_with("child/test1")
        manager_with_root._managers[1].save.assert_called_once_with(
            manager_with_root._managers[0].get.return_value, "test2"
        )
        manager_with_root._managers[0].delete_file.assert_called_once_with(
            "child/test1"
        )
