"""
サンプル: ログイン → セキュアエリア確認 → ログアウト

実行方法:
    cd F:\dev\original_libs
    python -m examples.sample_login.run
"""

from src.selenium.driver import EdgeDriver
from examples.sample_login.pages.login_page import LoginPage
from examples.sample_login.pages.secure_page import SecurePage

DRIVER_PATH = r"C:\Users\Public\Documents\msedgedriver.exe"


def main() -> None:
    with EdgeDriver(driver_path=DRIVER_PATH) as d:

        # ログイン画面を開く
        login = LoginPage(d.driver)
        login.open()

        # 正しい認証情報でログイン
        login.login(username="tomsmith", password="SuperSecretPassword!")

        # ログイン後の画面を確認
        secure = SecurePage(d.driver)
        print("画面見出し:", secure.get_heading())
        print("メッセージ:", secure.get_flash_message())

        # ログアウト
        secure.logout()
        print("ログアウト完了")

        # ログアウト後はログイン画面に戻る
        login_again = LoginPage(d.driver)
        print("ログアウト後メッセージ:", login_again.get_flash_message())


if __name__ == "__main__":
    main()
