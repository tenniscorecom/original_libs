from src.selenium.base_page import BasePage


class LoginPage(BasePage):
    """ログイン画面。"""

    URL = "https://the-internet.herokuapp.com/login"

    def open(self) -> None:
        self._driver.get(self.URL)

    def login(self, username: str, password: str) -> None:
        self.input_id("username", username)
        self.input_id("password", password)
        self.click_css(".radius")

    def get_error_message(self) -> str:
        return self.text_css("#flash")
