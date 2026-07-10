from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

from .options import BrowserOptions


class EdgeDriver:
    """Edge WebDriver のラッパー。with 文で確実に終了できる。

    Args:
        browser_options: BrowserOptions のインスタンス。省略時はデフォルト設定で起動。
                         DRIVER_PATH / WAIT_SECONDS もここで設定する。
    """

    def __init__(self, browser_options: BrowserOptions | None = None) -> None:
        opts = browser_options or BrowserOptions()

        options = Options()
        for arg in opts.build():
            options.add_argument(arg)

        service = Service(executable_path=opts.DRIVER_PATH)
        self._driver = webdriver.Edge(service=service, options=options)
        self._driver.implicitly_wait(opts.WAIT_SECONDS)

    def __enter__(self) -> "EdgeDriver":
        return self

    def __exit__(self, *args) -> None:
        self.quit()

    @property
    def driver(self) -> webdriver.Edge:
        return self._driver

    def quit(self) -> None:
        self._driver.quit()
