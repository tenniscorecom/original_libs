"""
selenium/base_page.py — Page Object の基底クラス

画面ごとに BasePage を継承したクラスを作り、その画面でできる操作をメソッドとして定義する。
セレクター種別（ID / name / CSS / XPath）をメソッド名に含めるため、By のインポートが不要。

使い方:
    1. 画面クラスを作る
        from src.selenium.base_page import BasePage

        class LoginPage(BasePage):
            URL = "https://example.com/login"

            def open(self) -> None:
                self._driver.get(self.URL)

            def login(self, username: str, password: str) -> None:
                self.input_id("username", username) # id="username" に入力
                self.input_id("password", password)
                self.click_id("login-btn") # id="login-btn" をクリック

            def get_error(self) -> str:
                return self.text_css(".error-message") # CSS セレクターでテキスト取得

    2. EdgeDriver と組み合わせて使う
        from src.selenium.driver import EdgeDriver

        with EdgeDriver(driver_path=r"C:\\...\\msedgedriver.exe") as d:
            page = LoginPage(d.driver)
            page.open()
            page.login("yamada", "password123")

セレクターの優先順位:
    1. ID（click_id / input_id / text_id）
    2. name 属性（click_name / input_name / text_name）
    3. CSS セレクター（click_css / input_css / text_css）
    4. XPath（click_xpath / input_xpath / text_xpath）← 最終手段。絶対パスは使わない
"""

import datetime
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    """全 Page Object の基底クラス。画面ごとにこのクラスを継承して使う。

    要素が見つかるまで wait_seconds 秒まで自動で待機する（暗黙的待機）。
    """

    def __init__(self, driver: WebDriver, wait_seconds: int = 10) -> None:
        """
        Args:
            driver: WebDriver インスタンス（EdgeDriver.driver から取得）。
            wait_seconds: 要素待機のタイムアウト秒数。
        """
        self._driver = driver
        self._wait = WebDriverWait(driver, wait_seconds)

    def open(self, url: str) -> None:
        """指定した URL を開く。"""
        self._driver.get(url)

    def save_screenshot(self, prefix: str = "error") -> Path:
        """スクリーンショットを logs/ フォルダに保存する。

        エラー発生時の状態記録に使う。

        Args:
            prefix: ファイル名のプレフィックス（デフォルト: "error"）。
                    保存先: logs/{prefix}_{YYYYmmdd_HHMMSS}.png

        Returns:
            保存したファイルのパス。
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path("logs") / f"{prefix}_{timestamp}.png"
        path.parent.mkdir(exist_ok=True)
        self._driver.save_screenshot(str(path))
        return path

    # ------------------------------------------------------------------ click
    def click_id(self, value: str) -> None:
        """id 属性でクリックする。"""
        self._click(By.ID, value)

    def click_name(self, value: str) -> None:
        """name 属性でクリックする。"""
        self._click(By.NAME, value)

    def click_css(self, value: str) -> None:
        """CSS セレクターでクリックする。"""
        self._click(By.CSS_SELECTOR, value)

    def click_xpath(self, value: str) -> None:
        """XPath でクリックする。"""
        self._click(By.XPATH, value)

    # ------------------------------------------------------------------ input
    def input_id(self, value: str, text: str) -> None:
        """id 属性の入力欄にテキストを入力する（既存の値はクリアされる）。"""
        self._input(By.ID, value, text)

    def input_name(self, value: str, text: str) -> None:
        """name 属性の入力欄にテキストを入力する（既存の値はクリアされる）。"""
        self._input(By.NAME, value, text)

    def input_css(self, value: str, text: str) -> None:
        """CSS セレクターの入力欄にテキストを入力する（既存の値はクリアされる）。"""
        self._input(By.CSS_SELECTOR, value, text)

    def input_xpath(self, value: str, text: str) -> None:
        """XPath の入力欄にテキストを入力する（既存の値はクリアされる）。"""
        self._input(By.XPATH, value, text)

    # ---------------------------------------------------------------- get_text
    def text_id(self, value: str) -> str:
        """id 属性の要素のテキストを返す。"""
        return self._text(By.ID, value)

    def text_name(self, value: str) -> str:
        """name 属性の要素のテキストを返す。"""
        return self._text(By.NAME, value)

    def text_css(self, value: str) -> str:
        """CSS セレクターの要素のテキストを返す。"""
        return self._text(By.CSS_SELECTOR, value)

    def text_xpath(self, value: str) -> str:
        """XPath の要素のテキストを返す。"""
        return self._text(By.XPATH, value)

    # ----------------------------------------------------------- private base
    def _click(self, by: str, value: str) -> None:
        self._wait.until(EC.element_to_be_clickable((by, value))).click()

    def _input(self, by: str, value: str, text: str) -> None:
        el = self._wait.until(EC.visibility_of_element_located((by, value)))
        el.clear()
        el.send_keys(text)

    def _text(self, by: str, value: str) -> str:
        return self._wait.until(EC.visibility_of_element_located((by, value))).text
