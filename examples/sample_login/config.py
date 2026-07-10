from src.config import Config


class AppConfig(Config):
    """プロジェクト固有の設定クラス。

    - config.ini         → プロジェクト設定（パス・URL など）
    - browser_options.ini → Selenium ブラウザオプションの差分だけ記述
    """

    def __init__(self) -> None:
        super().__init__("config.ini")
        self._browser = Config("browser_options.ini")

    @property
    def add_args(self) -> list[str]:
        """browser_options.ini の add をリストで返す。"""
        return self.parse_list(getattr(self._browser.OPTIONS, "ADD", ""))

    @property
    def remove_args(self) -> list[str]:
        """browser_options.ini の remove をリストで返す。"""
        return self.parse_list(getattr(self._browser.OPTIONS, "REMOVE", ""))


config = AppConfig()
