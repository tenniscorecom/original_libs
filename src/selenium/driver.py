from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

from .options import BrowserOptions


class EdgeDriver:
    """Edge WebDriver のラッパー。with 文で確実に終了できる。

    Args:
        driver_path:      msedgedriver.exe のパス
        wait_seconds:     暗黙的待機（秒）
        browser_options:  BrowserOptions のインスタンス。省略時はデフォルト設定で起動。
    """

    def __init__(
        self,
        driver_path: str,
        wait_seconds: int = 10,
        browser_options: BrowserOptions | None = None,
    ) -> None:
        opts_builder = browser_options or BrowserOptions()

        options = Options()
        for arg in opts_builder.build():
            options.add_argument(arg)

        service = Service(executable_path=driver_path)
        self._driver = webdriver.Edge(service=service, options=options)
        self._driver.implicitly_wait(wait_seconds)

    def __enter__(self) -> "EdgeDriver":
        return self

    def __exit__(self, *args) -> None:
        self.quit()

    @property
    def driver(self) -> webdriver.Edge:
        return self._driver

    def quit(self) -> None:
        self._driver.quit()
