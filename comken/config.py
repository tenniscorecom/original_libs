"""
config.py — INI ファイル読み込みユーティリティ

config.ini を読み込み、config.SECTION.KEY の形式でアクセスできる Config クラスを提供する。

プロジェクト側での使い方:
    src/config.py でシングルトンを作り、各モジュールからインポートする。

        # src/config.py
        from comken.config import Config
        config = Config()

        # 各モジュール
        from .config import config
        path = config.FILES.CSV_INPUT_FOLDER / config.FILES.CSV_EAST

※ ブラウザの設定は config.ini ではなく BrowserOptions のインスタンス
   （src/browser_options.py）で行う。config はブラウザ設定を持たない。
"""

import configparser
import types
from pathlib import Path

from .exceptions import ConfigError


def _parse_value(cfg: configparser.ConfigParser, section: str, key: str) -> bool | int | float | Path | str:
    """ini の値を適切な Python 型に変換して返す。

    変換の優先順位:
        1. true / false（大文字小文字問わず）→ bool
        2. 絶対パス（C:\\ / \\\\ / / で始まる）→ Path
        3. 整数に変換できる → int
        4. 小数に変換できる → float
        5. それ以外 → str

    文字列として使いたい数値（例: シート名 "2024"）はコード側で str() に変換する。
    """
    value = cfg.get(section, key).strip()
    lower = value.lower()

    if lower == "true":
        return True
    if lower == "false":
        return False

    if len(value) >= 2 and (value[1:3] == ":\\" or value[:2] == "\\\\" or value[0] == "/"):
        return Path(value)

    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass

    return value


class Config:
    """config.ini を読み込み、config.SECTION.KEY の形式でアクセスできるクラス。

    値の型変換（_parse_value の変換順と同じ）:
        - true / false → bool
        - 絶対パス（C:\\ / \\\\ / /）→ Path
        - 整数 → int
        - 小数 → float
        - それ以外 → str

    数値を文字列として使いたい場合はコード側で str() に変換する。

    config.ini の例（セクション名・キー名は大文字で書く）:
        [BROWSER]
        WAIT_SECONDS = 10
        HEADLESS = false

        [FILES]
        INPUT_FOLDER = C:\\作業\\input

    使い方:
        config = Config() # カレントディレクトリの config.ini を読む
        config = Config("path/to/config.ini") # パスを指定する場合

        config.BROWSER.HEADLESS        # → False（bool）
        config.BROWSER.WAIT_SECONDS    # → 10（int）
        config.FILES.INPUT_FOLDER      # → Path("C:\\作業\\input")
        config.FILES.INPUT_FOLDER / "東日本.csv"  # → Path("C:\\作業\\input\\東日本.csv")
    """

    def __init__(self, path: str | Path = "config.ini") -> None:
        """
        Args:
            path: config.ini のパス。省略するとカレントディレクトリの config.ini を読む。
        """
        cfg = configparser.ConfigParser()
        loaded = cfg.read(path, encoding="utf-8")
        if not loaded:
            # configparser はファイルがなくても黙って空になるため、明示的にエラーにする
            # （後で config.FILES 等が分かりにくい AttributeError になるのを防ぐ）
            raise ConfigError(ConfigError.MSG.format(path=Path(path).resolve()))

        for section in cfg.sections():
            ns = types.SimpleNamespace(
                **{k.upper(): _parse_value(cfg, section, k) for k in cfg.options(section)}
            )
            setattr(self, section.upper(), ns)

    def parse_list(self, value: str) -> list[str]:
        """カンマまたは改行区切りの文字列をリストに変換する。空文字は除外する。

        config.ini でカンマ区切りや複数行の値を扱う場合に使う。

        config.ini の例:
            [REPORT]
            TARGET_SHEETS = 東日本, 西日本, 集計

        使い方:
            config.parse_list(config.REPORT.TARGET_SHEETS)
            # → ["東日本", "西日本", "集計"]

        Args:
            value: カンマまたは改行区切りの文字列。

        Returns:
            空文字を除いた文字列のリスト。
        """
        items = value.replace("\n", ",").split(",")
        return [s.strip() for s in items if s.strip()]
