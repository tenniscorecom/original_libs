"""
utils.py — 汎用ユーティリティ

使い方:
    from src.utils import local_copy, dated_filename, find_today_file, find_latest_file

    # NAS ファイルのローカルコピー
    with local_copy(r"\\nas-server\share\data.xlsx") as path:
        with ExcelFile(path) as f:
            rows = f.read_rows_as_dicts("Sheet1")

    # 日付ファイル名
    dated_filename("売上レポート")            # → "20260710_売上レポート.xlsx"
    dated_filename("売上レポート", pre=False) # → "売上レポート_20260710.xlsx"

    # 今日・最新のファイルを取得
    find_today_file(r"\\nas\share")           # → Path("20260710_売上レポート.xlsx")
    find_latest_file(r"\\nas\share")          # → 最も新しい .xlsx ファイル
"""

import datetime
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def local_copy(path: str | Path):
    """ネットワーク上のファイルをローカルにコピーし、処理後に自動削除する。

    NAS やネットワークドライブ上の大きなファイルを直接開くと遅い場合や、
    win32com（Excel COM）でネットワークファイルが不安定な場合に使う。

    テンポラリファイルの保存先: C:\\Users\\<ユーザー名>\\AppData\\Local\\Temp\\
    with ブロックを抜けると自動削除される（例外が発生した場合も削除される）。

    使い方:
        with local_copy(r"\\\\nas-server\\share\\data.xlsx") as local_path:
            with ExcelFile(local_path) as f:
                rows = f.read_rows_as_dicts("Sheet1")

    Args:
        path: コピー元のファイルパス（ネットワークパス・UNCパス・マップドドライブ）。

    Yields:
        ローカルのテンポラリファイルパス（Path）。
    """
    src = Path(path)
    tmp = tempfile.NamedTemporaryFile(suffix=src.suffix, delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()
    try:
        shutil.copy2(src, tmp_path)
        yield tmp_path
    finally:
        tmp_path.unlink(missing_ok=True)


def dated_filename(name: str, suffix: str = ".xlsx", pre: bool = True) -> str:
    """今日の日付を付けたファイル名を返す。

    使い方:
        dated_filename("売上レポート")            # → "20260710_売上レポート.xlsx"
        dated_filename("売上レポート", pre=False) # → "売上レポート_20260710.xlsx"
        dated_filename("ログ", suffix=".csv")     # → "20260710_ログ.csv"

    Args:
        name: ファイル名（拡張子なし）。
        suffix: 拡張子（デフォルト: ".xlsx"）。
        pre: True でプレフィックス、False でサフィックス。

    Returns:
        日付付きのファイル名文字列。
    """
    date = datetime.date.today().strftime("%Y%m%d")
    return f"{date}_{name}{suffix}" if pre else f"{name}_{date}{suffix}"


def find_today_file(folder: str | Path, pattern: str = "*.xlsx") -> Path | None:
    """フォルダ内から今日の日付（YYYYMMDD）を含むファイルを返す。

    該当ファイルが複数ある場合は更新日時が最も新しいものを返す。
    見つからない場合は None を返す。

    使い方:
        path = find_today_file(r"\\nas\share")
        if path is None:
            raise FileNotFoundError("今日のファイルが見つかりません")
        with ExcelFile(path) as f:
            rows = f.read_rows_as_dicts("Sheet1")

    Args:
        folder: 検索するフォルダのパス。
        pattern: ファイルのパターン（デフォルト: "*.xlsx"）。

    Returns:
        見つかったファイルの Path。見つからない場合は None。
    """
    today = datetime.date.today().strftime("%Y%m%d")
    matched = [p for p in Path(folder).glob(pattern) if today in p.name]
    if not matched:
        return None
    return max(matched, key=lambda p: p.stat().st_mtime)


def find_latest_file(folder: str | Path, pattern: str = "*.xlsx") -> Path | None:
    """フォルダ内から更新日時が最も新しいファイルを返す。

    見つからない場合は None を返す。

    使い方:
        path = find_latest_file(r"\\nas\share")
        if path is None:
            raise FileNotFoundError("ファイルが見つかりません")
        with ExcelFile(path) as f:
            rows = f.read_rows_as_dicts("Sheet1")

    Args:
        folder: 検索するフォルダのパス。
        pattern: ファイルのパターン（デフォルト: "*.xlsx"）。

    Returns:
        最も新しいファイルの Path。見つからない場合は None。
    """
    files = list(Path(folder).glob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)
