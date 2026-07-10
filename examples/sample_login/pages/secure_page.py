from comken.selenium.base_page import BasePage


class SecurePage(BasePage):
    """ログイン後のセキュアエリア画面。"""

    def get_heading(self) -> str:
        return self.text_css("h2")

    def get_flash_message(self) -> str:
        return self.text_css("#flash")

    def logout(self) -> None:
        self.click_css(".button.secondary.radius")
