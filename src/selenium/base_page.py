import datetime
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    """全 Page Object の基底クラス。"""

    def __init__(self, driver: WebDriver, wait_seconds: int = 10) -> None:
        self._driver = driver
        self._wait = WebDriverWait(driver, wait_seconds)

    def open(self, url: str) -> None:
        self._driver.get(url)

    def save_screenshot(self, prefix: str = "error") -> Path:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path("logs") / f"{prefix}_{timestamp}.png"
        path.parent.mkdir(exist_ok=True)
        self._driver.save_screenshot(str(path))
        return path

    # ------------------------------------------------------------------ click
    def click_id(self, value: str) -> None:
        self._click(By.ID, value)

    def click_name(self, value: str) -> None:
        self._click(By.NAME, value)

    def click_css(self, value: str) -> None:
        self._click(By.CSS_SELECTOR, value)

    def click_xpath(self, value: str) -> None:
        self._click(By.XPATH, value)

    # ------------------------------------------------------------------ input
    def input_id(self, value: str, text: str) -> None:
        self._input(By.ID, value, text)

    def input_name(self, value: str, text: str) -> None:
        self._input(By.NAME, value, text)

    def input_css(self, value: str, text: str) -> None:
        self._input(By.CSS_SELECTOR, value, text)

    def input_xpath(self, value: str, text: str) -> None:
        self._input(By.XPATH, value, text)

    # ---------------------------------------------------------------- get_text
    def text_id(self, value: str) -> str:
        return self._text(By.ID, value)

    def text_name(self, value: str) -> str:
        return self._text(By.NAME, value)

    def text_css(self, value: str) -> str:
        return self._text(By.CSS_SELECTOR, value)

    def text_xpath(self, value: str) -> str:
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
