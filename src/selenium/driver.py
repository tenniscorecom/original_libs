from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options


def create_driver(driver_path: str, wait_seconds: int = 10, headless: bool = False) -> webdriver.Edge:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(executable_path=driver_path)
    driver = webdriver.Edge(service=service, options=options)
    driver.implicitly_wait(wait_seconds)
    return driver
