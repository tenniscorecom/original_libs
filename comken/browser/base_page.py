"""
browser/base_page.py — Page Object の基底クラス

画面ごとに BasePage を継承したクラスを作り、その画面でできる操作をメソッドとして定義する。
セレクター種別（ID / name / CSS / XPath）をメソッド名に含めるため、By のインポートが不要。

使い方:
    1. 画面クラスを作る
        from comken.browser.base_page import BasePage

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
        from comken.browser.driver import EdgeDriver

        with EdgeDriver() as d:
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

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


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

    # --------------------------------------------------------------- select
    def select_text_id(self, value: str, text: str) -> None:
        """id 属性の <select> をテキストで選択する。"""
        self._select_text(By.ID, value, text)

    def select_text_name(self, value: str, text: str) -> None:
        """name 属性の <select> をテキストで選択する。"""
        self._select_text(By.NAME, value, text)

    def select_text_css(self, value: str, text: str) -> None:
        """CSS セレクターの <select> をテキストで選択する。"""
        self._select_text(By.CSS_SELECTOR, value, text)

    def select_text_xpath(self, value: str, text: str) -> None:
        """XPath の <select> をテキストで選択する。"""
        self._select_text(By.XPATH, value, text)

    def select_value_id(self, value: str, option_value: str) -> None:
        """id 属性の <select> を value 属性で選択する。"""
        self._select_value(By.ID, value, option_value)

    def select_value_name(self, value: str, option_value: str) -> None:
        """name 属性の <select> を value 属性で選択する。"""
        self._select_value(By.NAME, value, option_value)

    def select_value_css(self, value: str, option_value: str) -> None:
        """CSS セレクターの <select> を value 属性で選択する。"""
        self._select_value(By.CSS_SELECTOR, value, option_value)

    def select_value_xpath(self, value: str, option_value: str) -> None:
        """XPath の <select> を value 属性で選択する。"""
        self._select_value(By.XPATH, value, option_value)

    def select_index_id(self, value: str, index: int) -> None:
        """id 属性の <select> をインデックスで選択する（0始まり）。"""
        self._select_index(By.ID, value, index)

    def select_index_name(self, value: str, index: int) -> None:
        """name 属性の <select> をインデックスで選択する（0始まり）。"""
        self._select_index(By.NAME, value, index)

    def select_index_css(self, value: str, index: int) -> None:
        """CSS セレクターの <select> をインデックスで選択する（0始まり）。"""
        self._select_index(By.CSS_SELECTOR, value, index)

    def select_index_xpath(self, value: str, index: int) -> None:
        """XPath の <select> をインデックスで選択する（0始まり）。"""
        self._select_index(By.XPATH, value, index)

    def select_radio_name(self, name: str, value: str) -> None:
        """name 属性と value 属性でラジオボタンを選択する。

        Args:
            name: ラジオボタングループの name 属性。
            value: 選択する option の value 属性。
        """
        self._click(By.CSS_SELECTOR, f"input[type='radio'][name='{name}'][value='{value}']")

    # ------------------------------------------------------------------ alert
    def alert_accept(self) -> None:
        """アラートを承認（OK）する。アラートが表示されるまで待機する。"""
        self._wait.until(EC.alert_is_present()).accept()

    def alert_dismiss(self) -> None:
        """アラートをキャンセルする。アラートが表示されるまで待機する。"""
        self._wait.until(EC.alert_is_present()).dismiss()

    def alert_text(self) -> str:
        """アラートのテキストを返す。アラートが表示されるまで待機する。"""
        return self._wait.until(EC.alert_is_present()).text

    # ------------------------------------------------------------------- wait
    def wait_visible_id(self, value: str) -> None:
        """id 属性の要素が表示されるまで待機する（モーダルが開くのを待つ等）。"""
        self._wait.until(EC.visibility_of_element_located((By.ID, value)))

    def wait_visible_css(self, value: str) -> None:
        """CSS セレクターの要素が表示されるまで待機する。"""
        self._wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, value)))

    def wait_visible_xpath(self, value: str) -> None:
        """XPath の要素が表示されるまで待機する。"""
        self._wait.until(EC.visibility_of_element_located((By.XPATH, value)))

    def wait_invisible_css(self, value: str) -> None:
        """CSS セレクターの要素が非表示になるまで待機する（モーダルが閉じるのを待つ等）。"""
        self._wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, value)))

    def wait_invisible_xpath(self, value: str) -> None:
        """XPath の要素が非表示になるまで待機する。"""
        self._wait.until(EC.invisibility_of_element_located((By.XPATH, value)))

    # -------------------------------------------------------------------- has
    def has_id(self, value: str) -> bool:
        """id 属性の要素が DOM 上に存在するか返す（表示非表示は問わない）。"""
        return self._has(By.ID, value)

    def has_css(self, value: str) -> bool:
        """CSS セレクターの要素が DOM 上に存在するか返す。"""
        return self._has(By.CSS_SELECTOR, value)

    def has_xpath(self, value: str) -> bool:
        """XPath の要素が DOM 上に存在するか返す。"""
        return self._has(By.XPATH, value)

    # ----------------------------------------------------------------- scroll
    def scroll_to_css(self, value: str) -> None:
        """CSS セレクターの要素が見えるようにスクロールする。"""
        el = self._driver.find_element(By.CSS_SELECTOR, value)
        self._driver.execute_script("arguments[0].scrollIntoView(true);", el)

    def scroll_to_id(self, value: str) -> None:
        """id 属性の要素が見えるようにスクロールする。"""
        el = self._driver.find_element(By.ID, value)
        self._driver.execute_script("arguments[0].scrollIntoView(true);", el)

    def scroll_bottom(self) -> None:
        """ページの一番下までスクロールする（無限スクロールのトリガー等）。"""
        self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # --------------------------------------------------------------- drag_drop
    def drag_drop_css(self, source: str, target: str) -> None:
        """CSS セレクターで指定した要素をドラッグ＆ドロップする。

        Args:
            source: ドラッグ元の CSS セレクター。
            target: ドロップ先の CSS セレクター。
        """
        src = self._wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, source)))
        tgt = self._wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, target)))
        ActionChains(self._driver).drag_and_drop(src, tgt).perform()

    # --------------------------------------------------------------------- js
    def js(self, script: str, *args) -> object:
        """JavaScript を実行する。

        Args:
            script: 実行する JavaScript 文字列。
            *args: スクリプト内で arguments[0], arguments[1] ... として参照できる引数。

        Returns:
            JavaScript の return 値。
        """
        return self._driver.execute_script(script, *args)

    # ----------------------------------------------------------- private base
    def _click(self, by: str, value: str) -> None:
        self._wait.until(EC.element_to_be_clickable((by, value))).click()

    def _input(self, by: str, value: str, text: str) -> None:
        el = self._wait.until(EC.visibility_of_element_located((by, value)))
        el.clear()
        el.send_keys(text)

    def _text(self, by: str, value: str) -> str:
        return self._wait.until(EC.visibility_of_element_located((by, value))).text

    def _select_text(self, by: str, value: str, text: str) -> None:
        el = self._wait.until(EC.visibility_of_element_located((by, value)))
        Select(el).select_by_visible_text(text)

    def _select_value(self, by: str, value: str, option_value: str) -> None:
        el = self._wait.until(EC.visibility_of_element_located((by, value)))
        Select(el).select_by_value(option_value)

    def _select_index(self, by: str, value: str, index: int) -> None:
        el = self._wait.until(EC.visibility_of_element_located((by, value)))
        Select(el).select_by_index(index)

    def _has(self, by: str, value: str) -> bool:
        try:
            self._driver.find_element(by, value)
            return True
        except NoSuchElementException:
            return False
