"""
config.py — INI ファイル読み込みユーティリティ

config.ini を読み込み、config.SECTION.KEY の形式でアクセスできる Config クラスを提供する。

プロジェクト側での使い方:
    1. Config をそのまま使う場合
        from src.config import Config
        config = Config()
        config.FILES.INPUT_FOLDER

    2. プロジェクト固有の設定を追加する場合（推奨）
        class AppConfig(Config):
            @property
            def edge_options(self) -> list[str]:
                return self.parse_list(self.BROWSER_OPTIONS.ADD)

        config = AppConfig()
"""

import configparser
import types
from pathlib import Path


def _parse_value(cfg: configparser.ConfigParser, section: str, key: str) -> bool | str:
    """boolean として解釈できる値は bool に変換し、それ以外は文字列のまま返す。

    true / false / yes / no / on / off / 1 / 0 が対象（大文字小文字問わず）。
    """
    try:
        return cfg.getboolean(section, key)
    except ValueError:
        return cfg.get(section, key)


class Config:
    """config.ini を読み込み、config.SECTION.KEY の形式でアクセスできるクラス。

    値の型変換:
        - boolean（true/false/yes/no/on/off/1/0）→ 自動で bool に変換
        - int / float → プロジェクト側で変換する（例: int(config.BROWSER.WAIT_SECONDS)）
        - それ以外 → str のまま返す

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
            [BROWSER_OPTIONS]
            ADD = --disable-gpu, --disable-extensions

        使い方:
            config.parse_list(config.BROWSER_OPTIONS.ADD)
            # → ["--disable-gpu", "--disable-extensions"]

        Args:
            value: カンマまたは改行区切りの文字列。

        Returns:
            空文字を除いた文字列のリスト。
        """
        items = value.replace("\n", ",").split(",")
        return [s.strip() for s in items if s.strip()]
