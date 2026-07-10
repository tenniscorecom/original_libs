import configparser
import types
from pathlib import Path


def _parse_value(cfg: configparser.ConfigParser, section: str, key: str) -> bool | str:
    """boolean として解釈できる値は bool に変換し、それ以外は文字列のまま返す。
    true/false/yes/no/on/off/1/0 が対象（大文字小文字問わず）。
    """
    try:
        return cfg.getboolean(section, key)
    except ValueError:
        return cfg.get(section, key)


class Config:
    """config.ini を読み込み、config.SECTION.KEY の形式でアクセスできるクラス。

    - boolean値（true/false/yes/no/on/off）は自動で bool に変換される
    - int/float はプロジェクト側で変換する（例: int(config.BROWSER.WAIT_SECONDS)）

    Usage:
        from src.config import Config

        config = Config()                      # カレントディレクトリの config.ini
        config = Config("path/to/config.ini")

        config.FILES.INPUT_FOLDER     # str
        config.BROWSER.HEADLESS       # bool（"true" → True）
        config.BROWSER.WAIT_SECONDS   # str → int(config.BROWSER.WAIT_SECONDS) で変換
    """

    def __init__(self, path: str | Path = "config.ini") -> None:
        cfg = configparser.ConfigParser()
        cfg.read(path, encoding="utf-8")

        for section in cfg.sections():
            ns = types.SimpleNamespace(
                **{k.upper(): _parse_value(cfg, section, k) for k in cfg.options(section)}
            )
            setattr(self, section.upper(), ns)

    def parse_list(self, value: str) -> list[str]:
        """カンマまたは改行区切りの文字列をリストに変換する。空文字は除外する。

        Usage:
            # config.ini
            # [browser_options]
            # add = --disable-gpu, --disable-extensions

            config.parse_list(config.BROWSER_OPTIONS.ADD)
            # → ["--disable-gpu", "--disable-extensions"]
        """
        items = value.replace("\n", ",").split(",")
        return [s.strip() for s in items if s.strip()]
