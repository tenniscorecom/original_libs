from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

from .options import DEFAULT_ARGS


class EdgeDriver:
    """Edge WebDriver のラッパー。with 文で確実に終了できる。

    Args:
        driver_path:   msedgedriver.exe のパス
        wait_seconds:  暗黙的待機（秒）
        headless:      True でブラウザを非表示
        add_args:      デフォルトに追加する起動引数
        remove_args:   デフォルトから除外する起動引数
    """

    def __init__(
        self,
        driver_path: str,
        wait_seconds: int = 10,
        headless: bool = False,
        add_args: list[str] | None = None,
        remove_args: list[str] | None = None,
    ) -> None:
        active = set(DEFAULT_ARGS)
        if headless:
            active.add("--headless=new")
        if remove_args:
            active -= set(remove_args)
        if add_args:
            active |= set(add_args)

        options = Options()
        for arg in active:
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
