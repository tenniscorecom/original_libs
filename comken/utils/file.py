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
import logging
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


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




def move_file(src: str | Path, dst: str | Path) -> Path:
    """ファイルを移動する。

    shutil.move の分かりにくい点をなくしたラッパー:
        - dst が既存フォルダなら、その中に同名で移動する
        - それ以外はファイルパスとして扱う（親フォルダがなければ自動作成する）
        - 移動先に同名ファイルがあれば上書きする

    使い方:
        move_file("report.xlsx", r"C:\\作業\\output")               # フォルダの中へ
        move_file("report.xlsx", r"C:\\作業\\output\\売上.xlsx")     # 名前を変えて移動

    Args:
        src: 移動するファイルのパス。
        dst: 移動先（フォルダ、またはファイルパス）。

    Returns:
        移動後のファイルパス。
    """
    src = Path(src)
    dst = Path(dst)
    target = dst / src.name if dst.is_dir() else dst
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    shutil.move(str(src), str(target))
    return target


def copy_file(src: str | Path, dst: str | Path) -> Path:
    """ファイルをコピーする（更新日時などの属性も保持する）。

    ルールは move_file と同じ:
        - dst が既存フォルダなら、その中に同名でコピーする
        - それ以外はファイルパスとして扱う（親フォルダがなければ自動作成する）
        - コピー先に同名ファイルがあれば上書きする

    Args:
        src: コピーするファイルのパス。
        dst: コピー先（フォルダ、またはファイルパス）。

    Returns:
        コピー後のファイルパス。
    """
    src = Path(src)
    dst = Path(dst)
    target = dst / src.name if dst.is_dir() else dst
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)
    return target


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
