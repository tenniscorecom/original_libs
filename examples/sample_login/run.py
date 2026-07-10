"""
サンプル: ログイン → セキュアエリア確認 → ログアウト

実行方法:
    cd F:\dev\original_libs
    python -m examples.sample_login.run
"""

from comken.browser.driver import EdgeDriver

from examples.sample_login.browser_options import SampleBrowserOptions
from examples.sample_login.pages.login_page import LoginPage

USERNAME = "tomsmith"
PASSWORD = "SuperSecretPassword!"


def main() -> None:
    with EdgeDriver(browser_options=SampleBrowserOptions()) as d:

        # LoginPage を作って開く
        login = LoginPage(d.driver)
        login.open()

        # login() は SecurePage を返す → そのまま次の画面の操作が書ける
        secure = login.login(username=USERNAME, password=PASSWORD)
        print("画面見出し:", secure.get_heading())
        print("メッセージ:", secure.get_flash_message())

        # logout() は LoginPage を返す
        login = secure.logout()
        print("ログアウト完了")


if __name__ == "__main__":
    main()
