import datetime
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    """全 Page Object の基底クラス。共通操作をまとめる。"""

    def __init__(self, driver: WebDriver, wait_seconds: int = 10) -> None:
        self._driver = driver
        self._wait = WebDriverWait(driver, wait_seconds)

    def open(self, url: str) -> None:
        self._driver.get(url)

    def click(self, by: str, value: str) -> None:
        self._wait.until(EC.element_to_be_clickable((by, value))).click()

    def input_text(self, by: str, value: str, text: str) -> None:
        el = self._wait.until(EC.visibility_of_element_located((by, value)))
        el.clear()
        el.send_keys(text)

    def get_text(self, by: str, value: str) -> str:
        return self._wait.until(EC.visibility_of_element_located((by, value))).text

    def save_screenshot(self, prefix: str = "error") -> Path:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path("logs") / f"{prefix}_{timestamp}.png"
        path.parent.mkdir(exist_ok=True)
        self._driver.save_screenshot(str(path))
        return path
