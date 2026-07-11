"""
config.py — INI ファイル読み込みユーティリティ

config.ini を読み込み、config.SECTION.KEY の形式でアクセスできる Config クラスを提供する。

プロジェクト側での使い方:
    1. Config をそのまま使う場合
        from comken.config import Config
        config = Config()
        config.FILES.INPUT_FOLDER

    2. プロジェクト固有の設定を追加する場合（推奨）
        class AppConfig(Config):
            @property
            def input_csv_path(self) -> Path:
                return Path(self.FILES.INPUT_FOLDER) / self.FILES.CSV_NAME

        config = AppConfig()

※ ブラウザの設定は config.ini ではなく BrowserOptions のサブクラス
   （src/browser_options.py）で行う。config はブラウザ設定を持たない。
"""

import configparser
import types
from pathlib import Path


def _parse_value(cfg: configparser.ConfigParser, section: str, key: str) -> bool | str:
    """値が true / false のときだけ bool に変換し、それ以外は文字列のまま返す。

    yes / no / on / off / 1 / 0 は変換しない
    （"1" が数値なのか bool なのか曖昧になる事故を避けるため）。
    大文字小文字は問わない（True / FALSE 等も変換される）。
    """
    value = cfg.get(section, key)
    lowered = value.strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return value


class Config:
    """config.ini を読み込み、config.SECTION.KEY の形式でアクセスできるクラス。

    値の型変換:
        - true / false（大文字小文字問わず）→ 自動で bool に変換
        - それ以外はすべて str のまま返す
          （yes / no / on / off / 1 / 0 も変換しない。
           int / float が必要ならプロジェクト側で変換する: int(config.BROWSER.WAIT_SECONDS)）

    config.ini の例（セクション名・キー名は大文字で書く）:
        [BROWSER]
        WAIT_SECONDS = 10
        HEADLESS = false

        [FILES]
        INPUT_FOLDER = C:\\作業\\input

    使い方:
        config = Config() # カレントディレクトリの config.ini を読む
        config = Config("path/to/config.ini") # パスを指定する場合

        config.BROWSER.HEADLESS # → False（bool に自動変換）
        config.BROWSER.WAIT_SECONDS # → "10"（str のまま）
        int(config.BROWSER.WAIT_SECONDS) # → 10（必要なら呼び出し側で変換）
    """

    def __init__(self, path: str | Path = "config.ini") -> None:
        """
        Args:
            path: config.ini のパス。省略するとカレントディレクトリの config.ini を読む。
        """
        cfg = configparser.ConfigParser()
        cfg.read(path, encoding="utf-8")

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
