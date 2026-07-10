import csv


class CsvReader:
    """CSV ファイルの読み込みユーティリティ。

    Usage:
        reader = CsvReader("data.csv")

        reader.rows()                          # 全行
        reader.rows(columns=["名前", "金額"]) # 特定列のみ
        reader.find("注文番号", "A001")        # キーで1件検索
        reader.filter("ステータス", "完了")    # キーで複数行検索
        reader.column("金額")                  # 列の値一覧
        reader.index("注文番号")               # キー列でインデックス化
    """

    def __init__(self, path: str, encoding: str = "utf-8-sig") -> None:
        self._path = path
        self._encoding = encoding

    def _load(self) -> list[dict[str, str]]:
        with open(self._path, encoding=self._encoding, newline="") as f:
            return list(csv.DictReader(f))

    def rows(self, columns: list[str] | None = None) -> list[dict[str, str]]:
        """全行を返す。columns を指定すると特定列のみ抽出する。"""
        data = self._load()
        if columns is None:
            return data
        return [{col: row[col] for col in columns if col in row} for row in data]

    def find(self, key_col: str, value: str) -> dict[str, str] | None:
        """key_col が value に一致する最初の行を返す。見つからなければ None。"""
        for row in self._load():
            if row.get(key_col) == value:
                return row
        return None

    def filter(self, key_col: str, value: str) -> list[dict[str, str]]:
        """key_col が value に一致する全行を返す。"""
        return [row for row in self._load() if row.get(key_col) == value]

    def column(self, col_name: str) -> list[str]:
        """指定列の値一覧を返す。"""
        return [row[col_name] for row in self._load() if col_name in row]

    def index(self, key_col: str) -> dict[str, dict[str, str]]:
        """key_col をキーにした辞書を返す。キーが重複する場合は後の行で上書き。"""
        return {row[key_col]: row for row in self._load() if key_col in row}
