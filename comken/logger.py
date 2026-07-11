"""
logger.py — ロガーの初期化

プロジェクトの main.py で1回だけ呼び、以降サブモジュールは
logging.getLogger(__name__) を使えばそのまま出力される。

- logs/名前_YYYYMMDD.log に DEBUG 以上を出力（日別ファイル）
- コンソールには INFO 以上を出力

使い方:
    # main.py
    from comken import setup_logger

    logger = setup_logger("main")
    logger.info("処理開始")

    # src/ 以下のモジュール
    import logging
    logger = logging.getLogger(__name__)
"""

import datetime
import logging
from pathlib import Path


def setup_logger(name: str = "main", log_dir: str | Path = "logs") -> logging.Logger:
    """ルートロガーにファイル・コンソールのハンドラを設定して返す。

    Args:
        name: ログファイル名の先頭に付く名前（例: "main" → logs/main_20260711.log）。
        log_dir: ログの出力先フォルダ。なければ作成する。

    Returns:
        name のロガー。
    """
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    log_file = log_path / f"{name}_{datetime.datetime.now():%Y%m%d}.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    # 二重に呼ばれてもハンドラが重複しない（ログが2重に出ない）ようにする。
    # close() してから外す（clear だけだとログファイルが開きっぱなしになる）
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    return logging.getLogger(name)
