"""
csv/writer.py — CSV 書き込みユーティリティ

CsvWriter クラスを通じて CSV ファイルへの書き込みを行う。

使い方:
    from comken.csv import CsvWriter

    rows = [{"注文番号": "A001", "金額": "1000"}, {"注文番号": "A002", "金額": "2000"}]

    # 新規作成（上書き）
    writer = CsvWriter("output.csv", fieldnames=["注文番号", "金額"])
    writer.write_rows(rows)

    # 既存ファイルに追記
    writer = CsvWriter("output.csv", fieldnames=["注文番号", "金額"])
    writer.append_row({"注文番号": "A003", "金額": "3000"})
"""

import csv
from pathlib import Path

from .handler import Encoding


class CsvWriter:
    """CSV ファイルへの書き込みユーティリティ。

    使い方:
        rows = [{"氏名": "山田", "金額": "1000"}, {"氏名": "佐藤", "金額": "2000"}]

        # 新規作成
        writer = CsvWriter("output.csv", fieldnames=["氏名", "金額"])
        writer.write_rows(rows)

        # 1行追記
        writer.append_row({"氏名": "田中", "金額": "3000"})
    """

    def __init__(
        self,
        path: str | Path,
        fieldnames: list[str],
        encoding: str = Encoding.UTF8_SIG,
    ) -> None:
        """
        Args:
            path: 書き込み先の CSV ファイルパス。親フォルダがなければ書き込み時に自動作成される。
            fieldnames: ヘッダー行の列名リスト。書き込み順に影響する。
            encoding: 文字コード。Excel で開く場合は Encoding.UTF8_SIG（デフォルト）。
                      Shift-JIS が必要な場合は Encoding.CP932 を指定する。
                      Encoding.AUTO は自動判定できない（読み込み専用）ため UTF8_SIG として扱う。
        """
        # AUTO は読み込み時の自動判定用。書き込みではデフォルトの UTF8_SIG に揃える
        # （CsvReader と同じ定数を渡し回しても落ちないようにする）
        if encoding == Encoding.AUTO:
            encoding = Encoding.UTF8_SIG
        self._path = Path(path)
        self._fieldnames = fieldnames
        self._encoding = encoding

    def _open(self, mode: str):
        """親フォルダを作ってからファイルを開く（ExcelFile.save と挙動を揃える）。"""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        return open(self._path, mode, encoding=self._encoding, newline="")

    def write_rows(self, rows: list[dict]) -> None:
        """ファイルを新規作成（または上書き）して全行を書き込む。

        既存ファイルがある場合は上書きされる。

        Args:
            rows: 書き込む行のリスト（辞書のリスト）。
        """
        with self._open("w") as f:
            writer = csv.DictWriter(f, fieldnames=self._fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    def append_row(self, row: dict) -> None:
        """既存ファイルの末尾に1行追記する。

        ファイルが存在しない場合はヘッダー付きで新規作成する。

        Args:
            row: 追記する行の辞書。
        """
        is_new = not self._path.exists()
        with self._open("a") as f:
            writer = csv.DictWriter(f, fieldnames=self._fieldnames, extrasaction="ignore")
            if is_new:
                writer.writeheader()
            writer.writerow(row)

    def append_rows(self, rows: list[dict]) -> None:
        """既存ファイルの末尾に複数行追記する。

        ファイルが存在しない場合はヘッダー付きで新規作成する。

        Args:
            rows: 追記する行のリスト（辞書のリスト）。
        """
        is_new = not self._path.exists()
        with self._open("a") as f:
            writer = csv.DictWriter(f, fieldnames=self._fieldnames, extrasaction="ignore")
            if is_new:
                writer.writeheader()
            writer.writerows(rows)
