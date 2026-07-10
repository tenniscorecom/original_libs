"""
サンプル: ログイン → セキュアエリア確認 → ログアウト

実行方法:
    cd F:\dev\original_libs
    python -m examples.sample_login.run
"""

from src.selenium.driver import EdgeDriver
from examples.sample_login.browser_options import SampleBrowserOptions
from examples.sample_login.config import config
from examples.sample_login.pages.login_page import LoginPage
from examples.sample_login.pages.secure_page import SecurePage

# サンプルサイトの認証情報（https://the-internet.herokuapp.com/login）
USERNAME = "tomsmith"
PASSWORD = "SuperSecretPassword!"


def main() -> None:
    with EdgeDriver(
        driver_path=config.BROWSER.DRIVER_PATH,
        wait_seconds=int(config.BROWSER.WAIT_SECONDS),
        browser_options=SampleBrowserOptions(),
    ) as d:

        login = LoginPage(d.driver)
        login.open()
        login.login(username=USERNAME, password=PASSWORD)

        secure = SecurePage(d.driver)
        print("画面見出し:", secure.get_heading())
        print("メッセージ:", secure.get_flash_message())

        secure.logout()
        print("ログアウト完了")


if __name__ == "__main__":
    main()
