from src.config import Config


class AppConfig(Config):
    """プロジェクト固有の設定クラス。Config を継承して computed プロパティを追加する。"""

    @property
    def add_args(self) -> list[str]:
        """config.ini の [browser_options] add をリストで返す。"""
        return self.parse_list(getattr(self.BROWSER_OPTIONS, "ADD", ""))

    @property
    def remove_args(self) -> list[str]:
        """config.ini の [browser_options] remove をリストで返す。"""
        return self.parse_list(getattr(self.BROWSER_OPTIONS, "REMOVE", ""))


config = AppConfig()
