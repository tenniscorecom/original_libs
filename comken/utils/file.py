"""
utils/file.py — ファイル操作ユーティリティ

使い方:
    from comken.utils import DownloadDir, FileFinder, FileNameBuilder, local_copy

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

    # ブラウザダウンロード用の一時フォルダ
    dl = DownloadDir()
    with EdgeDriver(download_dir=dl) as d:
        ...
        files = dl.wait()
    dl.remove()
"""

import datetime
import logging
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


class DownloadDir:
    """ブラウザダウンロード用のフォルダ。作成・完了待ち・削除をまとめて扱う。

    使い方:
        import shutil
        from comken.utils import DownloadDir

        dl = DownloadDir()                        # 一時フォルダを作成
        with EdgeDriver(download_dir=dl) as d:    # そのまま渡せる
            d.driver.get("https://example.com/download")
            ...  # ダウンロード操作
            files = dl.wait()                     # 完了まで待機

        shutil.move(str(files[0]), "output/report.xlsx")
        dl.remove()  # 不要なら削除（残したい場合は呼ばない）

    固定のフォルダに落としたい場合は path を指定する:
        dl = DownloadDir(path=r"C:\\作業\\downloads")  # なければ作成される
        # wait() は作成時点で既にあったファイルを無視し、
        # 新しく増えたファイルだけを完了対象にする
    """

    def __init__(self, prefix: str = "comken_dl_", path: str | Path | None = None) -> None:
        """
        Args:
            prefix: 一時フォルダ名のプレフィックス（path 指定時は使われない）。
            path: 使用するフォルダのパス。指定するとそのフォルダを使う（なければ作成）。
                  省略時は一時フォルダを新規作成する。
        """
        if path:
            self.path = Path(path)
            self.path.mkdir(parents=True, exist_ok=True)
            self._is_temp = False
        else:
            self.path = Path(tempfile.mkdtemp(prefix=prefix))
            self._is_temp = True
        # 既存フォルダを指定した場合、前回のファイルを wait() の完了対象にしないための記録
        self._initial_files = {p.name for p in self.path.iterdir() if p.is_file()}

    def __fspath__(self) -> str:
        # os.PathLike 対応。EdgeDriver(download_dir=dl) のように直接渡せるようにする
        return str(self.path)

    def wait(self, timeout: int = 30) -> list[Path]:
        """ダウンロードが完了するまで待機し、完了したファイルの一覧を返す。

        Edge/Chrome はダウンロード中のファイルを ".crdownload" 拡張子で保存する。
        この拡張子のファイルが消えたらダウンロード完了と判断する。
        DownloadDir 作成時点で既にあったファイルは対象外
        （固定フォルダに前回のファイルが残っていても誤検出しない）。

        Args:
            timeout: タイムアウトまでの秒数（デフォルト: 30秒）。

        Returns:
            新しくダウンロードされたファイルのパスリスト（更新日時順）。

        Raises:
            TimeoutError: timeout 秒以内にダウンロードが完了しなかった場合。
        """
        import time

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            in_progress = list(self.path.glob("*.crdownload")) + list(self.path.glob("*.tmp"))
            files = [
                p
                for p in self.path.iterdir()
                if p.is_file()
                and p.suffix not in (".crdownload", ".tmp")
                and p.name not in self._initial_files
            ]
            if files and not in_progress:
                return sorted(files, key=lambda p: p.stat().st_mtime)
            time.sleep(0.5)

        raise TimeoutError(f"ダウンロードが {timeout} 秒以内に完了しませんでした: {self.path}")

    def remove(self, force: bool = False) -> None:
        """フォルダごと削除する。ファイルを残したい場合は呼ばなくてよい。

        誤削除防止のため、path で指定した固定フォルダは削除せず警告を出す
        （自動作成した一時フォルダだけを削除する）。
        固定フォルダも本当に削除したい場合は force=True を指定する。

        Args:
            force: True にすると path 指定した固定フォルダも削除する。
        """
        if not self._is_temp and not force:
            logger.warning(
                "path 指定されたフォルダのため削除しません（削除するには remove(force=True)）: %s",
                self.path,
            )
            return
        shutil.rmtree(self.path, ignore_errors=True)


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


class SortBy:
    """FileFinder.latest() の by 引数に使う定数。"""

    NAME = "name"  # ファイル名の辞書順
    UPDATED = "updated"  # 更新日時順


class FileFinder:
    """フォルダからファイルを探して取得する。

    見つからない場合はデフォルトで FileNotFoundError を投げる
    （業務スクリプトでは「ファイルがない＝処理を止める」がほとんどのため）。
    「なければ None で続行したい」場合は required=False を指定する。

    使い方:
        path = FileFinder(r"\\\\nas\\share").today()          # 今日の日付を含むファイル
        path = FileFinder(r"\\\\nas\\share").latest("*.csv")  # 最新の CSV

        # 見つからなくても処理を続けたい場合
        path = FileFinder(r"\\\\nas\\share").today(required=False)
        if path is None:
            ...  # スキップ処理など
    """

    def __init__(self, folder: str | Path) -> None:
        """
        Args:
            folder: 検索するフォルダのパス。
        """
        self._folder = Path(folder)

    def today(
        self,
        pattern: str = "*.xlsx",
        date_format: str = "%Y%m%d",
        required: bool = True,
    ) -> Path | None:
        """ファイル名に今日の日付を含むファイルを返す。

        該当ファイルが複数ある場合は更新日時が最も新しいものを返す。

        Args:
            pattern: ファイルのパターン（デフォルト: "*.xlsx"）。
            date_format: 日付フォーマット（デフォルト: "%Y%m%d"。年月で探すなら "%Y%m"）。
            required: True（デフォルト）なら見つからないとき FileNotFoundError。
                      False なら None を返す。

        Raises:
            FileNotFoundError: required=True で該当ファイルがない場合。
        """
        today = datetime.date.today().strftime(date_format)
        matched = [p for p in self._folder.glob(pattern) if today in p.name]
        if not matched:
            if required:
                raise FileNotFoundError(
                    f"今日の日付（{today}）を含むファイルが見つかりません: "
                    f"{self._folder}\\{pattern}"
                )
            return None
        return max(matched, key=lambda p: p.stat().st_mtime)

    def latest(
        self,
        pattern: str = "*.xlsx",
        by: str = SortBy.NAME,
        required: bool = True,
    ) -> Path | None:
        """最新のファイルを返す。

        デフォルトは**ファイル名の辞書順で最後**のもの
        （"20260711_売上.xlsx" のような日付プレフィックス命名で「名前上の最新」を取る用途）。
        コピーや再保存で更新日時が変わっていても影響を受けない。
        更新日時で選びたい場合は by=SortBy.UPDATED を指定する。

        Args:
            pattern: ファイルのパターン（デフォルト: "*.xlsx"）。
            by: SortBy.NAME（ファイル名順・デフォルト）または SortBy.UPDATED（更新日時順）。
            required: True（デフォルト）なら見つからないとき FileNotFoundError。
                      False なら None を返す。

        Raises:
            FileNotFoundError: required=True で該当ファイルがない場合。
            ValueError: by に SortBy.NAME / SortBy.UPDATED 以外を指定した場合。
        """
        if by not in (SortBy.NAME, SortBy.UPDATED):
            raise ValueError(f"by には SortBy.NAME か SortBy.UPDATED を指定してください: {by}")

        files = list(self._folder.glob(pattern))
        if not files:
            if required:
                raise FileNotFoundError(
                    f"ファイルが見つかりません: {self._folder}\\{pattern}"
                )
            return None
        if by == SortBy.UPDATED:
            return max(files, key=lambda p: p.stat().st_mtime)
        return max(files, key=lambda p: p.name)
