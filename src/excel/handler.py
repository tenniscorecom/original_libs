from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet


class ExcelFile:
    """openpyxl ワークブックのラッパー。with 文で確実に閉じられる。

    数式の計算結果が必要な場合は read_computed_rows() を使う。
    キャッシュで読めなければ自動で win32com にフォールバックする。

    マクロを実行する場合は run_macro() を使う（常に win32com を使用）。
    """

    def __init__(self, path: str | Path, data_only: bool = False, read_only: bool = False) -> None:
        self._path = Path(path)
        self._wb: Workbook = load_workbook(self._path, data_only=data_only, read_only=read_only)

    def __enter__(self) -> "ExcelFile":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def sheet(self, name: str) -> Worksheet:
        if name not in self._wb.sheetnames:
            raise ValueError(f"シートが見つかりません: {name}  存在するシート: {self._wb.sheetnames}")
        return self._wb[name]

    def read_rows(self, sheet_name: str, min_row: int = 2) -> list[tuple]:
        """指定シートの行データをタプルのリストで返す。"""
        return list(self.sheet(sheet_name).iter_rows(min_row=min_row, values_only=True))

    def read_rows_as_dicts(self, sheet_name: str, header_row: int = 1) -> list[dict]:
        """ヘッダー行をキーとした辞書のリストで返す。"""
        ws = self.sheet(sheet_name)
        all_rows = list(ws.iter_rows(min_row=header_row, values_only=True))
        if not all_rows:
            return []
        headers = all_rows[0]
        return [dict(zip(headers, row)) for row in all_rows[1:]]

    def read_computed_rows(self, sheet_name: str, min_row: int = 2) -> list[tuple]:
        """数式の計算結果を含む行を読む。

        openpyxl のキャッシュ値を優先する。
        キャッシュが古いか数式文字列が残っている場合は win32com にフォールバックする。
        """
        try:
            wb = load_workbook(self._path, data_only=True, read_only=True)
            rows = list(wb[sheet_name].iter_rows(min_row=min_row, values_only=True))
            wb.close()
            has_formula = any(
                isinstance(cell, str) and cell.startswith("=")
                for row in rows for cell in row
            )
            if not has_formula:
                return rows
        except Exception:
            pass

        from ..windows.handler import ExcelComHandler
        with ExcelComHandler(self._path) as com:
            return com.read_rows(sheet_name, min_row)

    def write_cell(self, sheet_name: str, row: int, col: int, value) -> None:
        self.sheet(sheet_name).cell(row=row, column=col).value = value

    def save(self, path: str | Path | None = None) -> None:
        save_path = Path(path) if path else self._path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        self._wb.save(save_path)

    def run_macro(self, macro_name: str) -> None:
        """VBA マクロを実行する（常に win32com を使用）。"""
        from ..windows.handler import ExcelComHandler
        with ExcelComHandler(self._path) as com:
            com.run_macro(macro_name)

    def close(self) -> None:
        self._wb.close()
