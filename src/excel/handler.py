from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet


def open_workbook(path: str, data_only: bool = False, read_only: bool = False) -> Workbook:
    return load_workbook(path, data_only=data_only, read_only=read_only)


def get_sheet(wb: Workbook, sheet_name: str) -> Worksheet:
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"シートが見つかりません: {sheet_name}  存在するシート: {wb.sheetnames}")
    return wb[sheet_name]


def read_all_rows(ws: Worksheet, min_row: int = 2) -> list[tuple]:
    return list(ws.iter_rows(min_row=min_row, values_only=True))


def write_cell(ws: Worksheet, row: int, col: int, value) -> None:
    ws.cell(row=row, column=col).value = value


def save(wb: Workbook, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    wb.close()
