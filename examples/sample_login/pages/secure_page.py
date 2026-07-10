"""
secure_page.py — ログイン後のセキュアエリア画面
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .app_page import AppPage

if TYPE_CHECKING:
    from .login_page import LoginPage


class SecurePage(AppPage):
    """ログイン後のセキュアエリア画面（/secure）。"""

    HEADING_CSS = "h2"
    LOGOUT_BTN_CSS = ".button.secondary.radius"

    def get_heading(self) -> str:
        """画面の見出しテキストを返す。"""
        return self.text_css(self.HEADING_CSS)

    def logout(self) -> LoginPage:
        """ログアウトして LoginPage を返す。"""
        from .login_page import LoginPage  # ランタイム用

        self.click_css(self.LOGOUT_BTN_CSS)
        return LoginPage(self._driver)
