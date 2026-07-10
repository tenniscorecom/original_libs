import configparser
import types
from pathlib import Path


class Config:
    """config.ini を読み込み、config.SECTION.KEY の形式でアクセスできるクラス。

    Usage:
        config = Config()                      # カレントディレクトリの config.ini
        config = Config("path/to/config.ini")

        config.FILES.INPUT_FOLDER
        config.EXCEL.DATA_SHEET
    """

    def __init__(self, path: str | Path = "config.ini") -> None:
        cfg = configparser.ConfigParser()
        cfg.read(path, encoding="utf-8")

        for section in cfg.sections():
            ns = types.SimpleNamespace(**{k.upper(): v for k, v in cfg.items(section)})
            setattr(self, section.upper(), ns)
