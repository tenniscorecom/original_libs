"""
src/config.py — このプロジェクトの設定シングルトン

config.ini を1回だけ読み、どのモジュールからも同じ config を使えるようにする。
Config() を呼ぶと src/config.pyi（補完用スタブ）が自動生成されるので、
config.SECTION.KEY がエディタで型付き補完される。

使い方（各モジュール）:
    from .config import config

    path = config.FILES.INPUT_FOLDER / "data.csv"
    folder = config.REPORT.OUTPUT_FOLDER
"""

from comken.config import Config

config = Config()  # カレントディレクトリの config.ini を読む
