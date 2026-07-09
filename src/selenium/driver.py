from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service


class EdgeDriver:
    """Edge WebDriver のラッパー。with 文で確実に終了できる。"""

    def __init__(self, driver_path: str, wait_seconds: int = 10, headless: bool = False) -> None:
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

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
