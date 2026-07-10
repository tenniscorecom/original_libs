"""
browser/site_page.py — サイト固有の Page Object 基底クラス

BasePage（ブラウザ操作の道具箱）を継承し、BASE_URL と共通ナビゲーションを追加する。
プロジェクト側でさらに継承して、サイト固有の処理を追加する。

継承の構造:
    BasePage        ← ブラウザ操作（click / input / select / alert 等）
      └── SitePage  ← サイト固有（BASE_URL / 共通ヘッダー操作 / ログイン等）
            └── LoginPage / HomePage / ...  ← 各画面

使い方:
    # プロジェクト側でサイトごとのベースクラスを作る
    from comken.browser.site_page import SitePage

    class AppPage(SitePage):
        BASE_URL = "https://example.com"

        def logout(self) -> None:
            self.click_css(".logout-btn")

    # 各画面は AppPage を継承する
    class LoginPage(AppPage):
        def open(self) -> None:
            self.go("/login")

        def login(self, username: str, password: str) -> "DashboardPage":
            self.input_id("username", username)
            self.input_id("password", password)
            self.click_id("login-btn")
            return DashboardPage(self._driver)  # 遷移先のクラスを返す

    class DashboardPage(AppPage):
        def get_title(self) -> str:
            return self.text_css("h1")
"""

from .base_page import BasePage


class SitePage(BasePage):
    """サイト固有の Page Object 基底クラス。

    BASE_URL を定義し、go() でサイト内の任意のパスに遷移できる。
    プロジェクト側でこのクラスを継承して、サイト固有の共通処理を追加する。

    画面遷移メソッドは遷移先のページクラスを返すことで、
    呼び出し側が画面の流れをコードで追えるようにする:
        dashboard = login_page.login("user", "pass")  # DashboardPage が返る
        title = dashboard.get_title()
    """

    BASE_URL: str = ""

    def go(self, path: str = "") -> None:
        """BASE_URL + path に遷移する。

        Args:
            path: BASE_URL からの相対パス（例: "/login", "/dashboard"）。
                  省略時は BASE_URL そのものに遷移する。
        """
        self._driver.get(self.BASE_URL + path)
