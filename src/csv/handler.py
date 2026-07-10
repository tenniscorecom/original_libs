"""
csv/handler.py — CSV 読み込みユーティリティ

CsvReader クラスを通じて CSV ファイルの読み込み・検索・抽出を行う。

使い方:
    from src.csv.handler import CsvReader

    reader = CsvReader("data.csv")
    reader.rows() # 全行を辞書のリストで取得
    reader.find("注文番号", "A001") # 1件検索
    reader.filter("ステータス", "完了") # 複数行検索
    reader.column("金額") # 列の値一覧
    reader.index("注文番号") # 辞書化（突合に使う）
"""

import csv
from pathlib import Path


class CsvReader:
    """CSV ファイルの読み込みユーティリティ。

    ヘッダー行をキーにした辞書のリストとして扱う。
    読み込みは各メソッド呼び出し時に毎回行う（キャッシュなし）。

    使い方:
        reader = CsvReader("東日本.csv")

        # 全行取得
        rows = reader.rows()
        # → [{"注文番号": "A001", "金額": "1000", "担当者": "山田"}, ...]

        # 特定列のみ取得
        rows = reader.rows(columns=["注文番号", "金額"])
        # → [{"注文番号": "A001", "金額": "1000"}, ...]

        # キーで1件検索
        row = reader.find("注文番号", "A001")
        # → {"注文番号": "A001", ...} または None（見つからない場合）

        # キーで複数行検索
        rows = reader.filter("担当者", "山田")

        # 列の値一覧
        amounts = reader.column("金額")
        # → ["1000", "2000", "3000"]

        # キー列でインデックス化（突合用辞書の作成）
        lookup = reader.index("注文番号")
        # → {"A001": {"注文番号": "A001", ...}, "A002": {...}}
    """

    def __init__(self, path: str | Path, encoding: str = "utf-8-sig") -> None:
        """
        Args:
            path: CSV ファイルのパス。
            encoding: 文字コード。BOM 付き UTF-8（Excel 出力など）は "utf-8-sig"（デフォルト）。
                      Shift-JIS の場合は "cp932" を指定する。
        """
        self._path = Path(path)
        self._encoding = encoding

    def _load(self) -> list[dict[str, str]]:
        with open(self._path, encoding=self._encoding, newline="") as f:
            return list(csv.DictReader(f))

    def rows(self, columns: list[str] | None = None) -> list[dict[str, str]]:
        """全行を返す。

        Args:
            columns: 取得する列名のリスト。省略すると全列を返す。

        Returns:
            辞書のリスト。columns 指定時は指定列のみ含む。
        """
        data = self._load()
        if columns is None:
            return data
        return [{col: row[col] for col in columns if col in row} for row in data]

    def find(self, key_col: str, value: str) -> dict[str, str] | None:
        """key_col が value に一致する最初の行を返す。

        Args:
            key_col: 検索対象の列名。
            value: 検索する値。

        Returns:
            一致した行の辞書。見つからない場合は None。
        """
        for row in self._load():
            if row.get(key_col) == value:
                return row
        return None

    def filter(self, key_col: str, value: str) -> list[dict[str, str]]:
        """key_col が value に一致する全行を返す。

        Args:
            key_col: 検索対象の列名。
            value: 検索する値。

        Returns:
            一致した行の辞書のリスト。一致しない場合は空リスト。
        """
        return [row for row in self._load() if row.get(key_col) == value]

    def column(self, col_name: str) -> list[str]:
        """指定列の値一覧を返す。

        Args:
            col_name: 取得する列名。

        Returns:
            列の値のリスト（ヘッダー行を除く）。
        """
        return [row[col_name] for row in self._load() if col_name in row]

    def index(self, key_col: str) -> dict[str, dict[str, str]]:
        """key_col をキーにした辞書を返す。

        Excel との突合など、キーで素早く行を引きたい場合に使う。
        キーが重複する場合は後の行で上書きされる。

        Args:
            key_col: キーとして使う列名。

        Returns:
            {キー値: 行の辞書} の形式の辞書。
        """
        return {row[key_col]: row for row in self._load() if key_col in row}
