"""
login_page.py — ログイン画面

【Page Object の書き方】
  - 画面に存在する要素のセレクターは定数（大文字）でクラス上部に定義する
  - メソッドは「この画面でできること」だけを書く
  - 別の画面に移動するメソッドは、遷移先のページクラスを返す

【循環インポートの対処】
  - TYPE_CHECKING ブロック: IDE・型チェッカー用（ランタイムでは評価されない）
  - メソッド内 lazy import: ランタイムで実際にクラスが必要になる場所だけインポート
  - from __future__ import annotations: 型注釈を文字列として扱い、実行時評価を避ける
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .app_page import AppPage

if TYPE_CHECKING:
    # IDE の補完・型チェック用。ランタイムでは import されない
    from .secure_page import SecurePage


class LoginPage(AppPage):
    """ログイン画面（/login）。"""

    # ── セレクター定数（F12 で確認した値をここに書く） ──
    PATH = "/login"
    USERNAME_ID = "username"
    PASSWORD_ID = "password"
    LOGIN_BTN_CSS = ".radius"
    ERROR_CSS = "#flash.error"

    def open(self) -> LoginPage:
        """ログイン画面を開き、自分自身を返す（メソッドチェーンできる）。

        使い方:
            secure = LoginPage(d.driver).open().login("user", "pass")
        """
        self.go(self.PATH)
        return self

    def login(self, username: str, password: str) -> SecurePage:
        """ログインして SecurePage を返す。

        画面遷移メソッドは遷移先のページクラスを返す。
        呼び出し側は返ってきたオブジェクトをそのまま使える:
            secure = login_page.login("user", "pass")
            print(secure.get_heading())
        """
        from .secure_page import SecurePage  # ランタイム用（循環参照を避けるためここでインポート）

        self.input_id(self.USERNAME_ID, username)
        self.input_id(self.PASSWORD_ID, password)
        self.click_css(self.LOGIN_BTN_CSS)
        return SecurePage(self._driver)

    def get_error_message(self) -> str:
        """ログイン失敗時のエラーメッセージを返す。"""
        return self.text_css(self.ERROR_CSS)
