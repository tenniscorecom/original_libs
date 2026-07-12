"""
EdgeDriver の委譲と BasePage の EdgeDriver 受け入れのテスト。

実際の Edge は起動せず、WebDriver をモックにして委譲の配線だけを確認する。
"""

from unittest.mock import MagicMock

import pytest

from comken.browser.base_page import BasePage
from comken.browser.driver import EdgeDriver


def _make_edge_driver(mock_webdriver) -> EdgeDriver:
    """Edge を起動せずに EdgeDriver を作る（委譲のテスト用）。"""
    d = EdgeDriver.__new__(EdgeDriver)
    d._driver = mock_webdriver
    return d


class TestEdgeDriverDelegation:
    """EdgeDriver → WebDriver の委譲のテスト。"""

    def test_open_calls_webdriver_get(self):
        """d.open(url) が WebDriver.get に委譲されることを確認する。"""
        mock = MagicMock()
        d = _make_edge_driver(mock)

        d.open("https://example.com")

        mock.get.assert_called_once_with("https://example.com")

    def test_find_element_delegates(self):
        """d.find_element が WebDriver に委譲され、返り値もそのまま返ることを確認する。"""
        mock = MagicMock()
        d = _make_edge_driver(mock)

        result = d.find_element("id", "login-btn")

        mock.find_element.assert_called_once_with("id", "login-btn")
        assert result is mock.find_element.return_value

    def test_properties_delegate(self):
        """current_url / title / page_source が WebDriver の値を返すことを確認する。"""
        mock = MagicMock()
        mock.current_url = "https://example.com/home"
        mock.title = "ホーム"
        mock.page_source = "<html></html>"
        d = _make_edge_driver(mock)

        assert d.current_url == "https://example.com/home"
        assert d.title == "ホーム"
        assert d.page_source == "<html></html>"

    def test_unwrapped_methods_delegate_via_getattr(self):
        """明示ラップしていない WebDriver のメソッドも d.xxx で呼べることを確認する。"""
        mock = MagicMock()
        d = _make_edge_driver(mock)

        d.set_window_size(1200, 800)

        mock.set_window_size.assert_called_once_with(1200, 800)

    def test_private_attribute_raises_instead_of_delegating(self):
        """_ 始まりの未定義属性は委譲せず AttributeError になることを確認する。

        （_driver 未設定時の無限再帰防止。copy / pickle の内部探索も誤委譲しない）
        """
        d = EdgeDriver.__new__(EdgeDriver)  # _driver 未設定の状態

        with pytest.raises(AttributeError):
            d._nonexistent

    def test_save_screenshot_accepts_path_object(self, tmp_path):
        """save_screenshot に Path を渡しても str に変換されて委譲されることを確認する。"""
        mock = MagicMock()
        d = _make_edge_driver(mock)
        target = tmp_path / "shot.png"

        d.save_screenshot(target)

        mock.save_screenshot.assert_called_once_with(str(target))


class TestBasePageAcceptsEdgeDriver:
    """BasePage が EdgeDriver をそのまま受け取れることのテスト。"""

    def test_unwraps_edge_driver(self):
        """LoginPage(d) のように EdgeDriver を渡すと中の WebDriver が使われることを確認する。"""
        mock = MagicMock(spec=[])  # .driver を持たない素の WebDriver 相当
        d = _make_edge_driver(mock)

        page = BasePage(d, wait_seconds=1)

        assert page._driver is mock

    def test_accepts_raw_webdriver(self):
        """従来どおり生の WebDriver も渡せることを確認する。"""
        mock = MagicMock(spec=[])  # .driver 属性なし

        page = BasePage(mock, wait_seconds=1)

        assert page._driver is mock
