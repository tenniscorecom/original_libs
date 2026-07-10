"""
utils/file.py — ファイル操作ユーティリティ

使い方:
    from comken.utils import FileFinder, FileNameBuilder, local_copy

    # NAS ファイルのローカルコピー
    with local_copy(r"\\\\nas-server\\share\\data.xlsx") as path:
        with ExcelFile(path) as f:
            rows = f.read_rows_as_dicts("Sheet1")

    # 日付付きファイル名の組み立て
    FileNameBuilder("売上レポート").prefix()   # → "20260711_売上レポート.xlsx"
    FileNameBuilder("売上レポート").suffix()   # → "売上レポート_20260711.xlsx"

    # フォルダからファイルを取得
    FileFinder(r"\\\\nas\\share").today()      # → 今日の日付を含むファイル
    FileFinder(r"\\\\nas\\share").latest()     # → 最も新しい .xlsx ファイル
"""

import datetime
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path


def make_download_dir(prefix: str = "comken_dl_") -> Path:
    """ブラウザダウンロード用の一時フォルダを作成して返す。

    EdgeDriver の download_dir 引数に渡して使う。
    フォルダの削除は呼び出し側で行う（残したい場合は削除しなくてよい）:

        dl_dir = make_download_dir()
        with EdgeDriver(download_dir=dl_dir) as d:
            ...  # ダウンロード操作
        files = list(dl_dir.glob("*.xlsx"))
        shutil.move(files[0], "output/")
        shutil.rmtree(dl_dir)  # 不要なら削除

    Args:
        prefix: フォルダ名のプレフィックス。

    Returns:
        作成した一時フォルダのパス。
    """
    return Path(tempfile.mkdtemp(prefix=prefix))


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


def wait_for_download(download_dir: str | Path, timeout: int = 30) -> list[Path]:
    """ダウンロードが完了するまで待機し、完了したファイルの一覧を返す。

    Edge/Chrome はダウンロード中のファイルを ".crdownload" 拡張子で保存する。
    この拡張子のファイルが消えたらダウンロード完了と判断する。

    使い方:
        import shutil
        from comken.utils import make_download_dir, wait_for_download

        dl_dir = make_download_dir()
        with EdgeDriver(download_dir=dl_dir) as d:
            d.driver.get("https://example.com/download")
            d.driver.find_element(By.ID, "download-btn").click()

            files = wait_for_download(dl_dir)  # 完了まで待機
            shutil.move(str(files[0]), "output/report.xlsx")

        shutil.rmtree(dl_dir)  # 不要なら削除

    Args:
        download_dir: ダウンロード先フォルダのパス。
        timeout: タイムアウトまでの秒数（デフォルト: 30秒）。

    Returns:
        ダウンロードされたファイルのパスリスト。

    Raises:
        TimeoutError: timeout 秒以内にダウンロードが完了しなかった場合。
    """
    import time

    dl_path = Path(download_dir)
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        in_progress = list(dl_path.glob("*.crdownload")) + list(dl_path.glob("*.tmp"))
        files = [p for p in dl_path.iterdir() if p.is_file() and p.suffix not in (".crdownload", ".tmp")]
        if files and not in_progress:
            return sorted(files, key=lambda p: p.stat().st_mtime)
        time.sleep(0.5)

    raise TimeoutError(f"ダウンロードが {timeout} 秒以内に完了しませんでした: {download_dir}")


class FileNameBuilder:
    """今日の日付を付けたファイル名を組み立てる。

    日付はファイル名の属性ではなく「付け方」なので、コンストラクタではなく
    prefix() / suffix() の呼び出し時に決める。

    使い方:
        FileNameBuilder("売上レポート").plain()                 # → "売上レポート.xlsx"
        FileNameBuilder("売上レポート").prefix()                # → "20260711_売上レポート.xlsx"
        FileNameBuilder("売上レポート").suffix()                # → "売上レポート_20260711.xlsx"
        FileNameBuilder("ログ", ext=".csv").prefix()            # → "20260711_ログ.csv"
        FileNameBuilder("月次").prefix(date_format="%Y%m")      # → "202607_月次.xlsx"
    """

    def __init__(self, name: str, ext: str = ".xlsx") -> None:
        """
        Args:
            name: ファイル名（拡張子なし）。
            ext: 拡張子（デフォルト: ".xlsx"）。
        """
        self._name = name
        self._ext = ext

    def plain(self) -> str:
        """日付なしのファイル名を返す。"""
        return f"{self._name}{self._ext}"

    def prefix(self, date_format: str = "%Y%m%d") -> str:
        """今日の日付を前に付けたファイル名を返す（例: 20260711_売上レポート.xlsx）。"""
        return f"{self._today(date_format)}_{self._name}{self._ext}"

    def suffix(self, date_format: str = "%Y%m%d") -> str:
        """今日の日付を後ろに付けたファイル名を返す（例: 売上レポート_20260711.xlsx）。"""
        return f"{self._name}_{self._today(date_format)}{self._ext}"

    @staticmethod
    def _today(date_format: str) -> str:
        return datetime.date.today().strftime(date_format)


class FileFinder:
    """フォルダからファイルを探して取得する。

    使い方:
        path = FileFinder(r"\\\\nas\\share").today()          # 今日の日付を含むファイル
        path = FileFinder(r"\\\\nas\\share").latest("*.csv")  # 最新の CSV

        if path is None:
            raise FileNotFoundError("ファイルが見つかりません")
    """

    def __init__(self, folder: str | Path) -> None:
        """
        Args:
            folder: 検索するフォルダのパス。
        """
        self._folder = Path(folder)

    def today(self, pattern: str = "*.xlsx", date_format: str = "%Y%m%d") -> Path | None:
        """ファイル名に今日の日付を含むファイルを返す。

        該当ファイルが複数ある場合は更新日時が最も新しいものを返す。
        見つからない場合は None を返す。

        Args:
            pattern: ファイルのパターン（デフォルト: "*.xlsx"）。
            date_format: 日付フォーマット（デフォルト: "%Y%m%d"。年月で探すなら "%Y%m"）。
        """
        today = datetime.date.today().strftime(date_format)
        matched = [p for p in self._folder.glob(pattern) if today in p.name]
        if not matched:
            return None
        return max(matched, key=lambda p: p.stat().st_mtime)

    def latest(self, pattern: str = "*.xlsx") -> Path | None:
        """更新日時が最も新しいファイルを返す。見つからない場合は None を返す。

        Args:
            pattern: ファイルのパターン（デフォルト: "*.xlsx"）。
        """
        files = list(self._folder.glob(pattern))
        if not files:
            return None
        return max(files, key=lambda p: p.stat().st_mtime)
