"""
utils.py — 汎用ユーティリティ

使い方:
    from src.utils import local_copy

    with local_copy(r"\\nas-server\share\data.xlsx") as path:
        with ExcelFile(path) as f:
            rows = f.read_rows_as_dicts("Sheet1")
    # with ブロックを抜けるとテンポラリファイルは自動削除される
"""

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
        # ここでテンポラリファイルは削除済み

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
