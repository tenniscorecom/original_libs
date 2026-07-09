from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet


class ExcelFile:
    """openpyxl ワークブックのラッパー。with 文で確実に閉じられる。"""

    def __init__(self, path: str, data_only: bool = False, read_only: bool = False) -> None:
        self._path = path
        self._wb: Workbook = load_workbook(path, data_only=data_only, read_only=read_only)

    def __enter__(self) -> "ExcelFile":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def sheet(self, name: str) -> Worksheet:
        if name not in self._wb.sheetnames:
            raise ValueError(f"シートが見つかりません: {name}  存在するシート: {self._wb.sheetnames}")
        return self._wb[name]

    def read_rows(self, sheet_name: str, min_row: int = 2) -> list[tuple]:
        return list(self.sheet(sheet_name).iter_rows(min_row=min_row, values_only=True))

    def write_cell(self, sheet_name: str, row: int, col: int, value) -> None:
        self.sheet(sheet_name).cell(row=row, column=col).value = value

    def save(self, path: str | None = None) -> None:
        save_path = path or self._path
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        self._wb.save(save_path)

    def close(self) -> None:
        self._wb.close()
