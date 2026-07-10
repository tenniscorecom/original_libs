import win32api
import win32com.client
import win32con
import win32gui
import pywintypes


class ExcelComHandler:
    """win32com を使った Excel 操作クラス。数式の計算結果を読む場合に使用する。"""

    def __init__(self, path: str, password: str = "") -> None:
        self._excel = win32com.client.Dispatch("Excel.Application")
        self._excel.Visible = False
        self._excel.DisplayAlerts = False
        kwargs = {"Filename": path}
        if password:
            kwargs["Password"] = password
        self._wb = self._excel.Workbooks.Open(**kwargs)
        self._excel.CalculateFull()

    def __enter__(self) -> "ExcelComHandler":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def sheet(self, name: str):
        return self._wb.Sheets(name)

    def read_cell(self, sheet_name: str, row: int, col: int):
        return self._wb.Sheets(sheet_name).Cells(row, col).Value

    def write_cell(self, sheet_name: str, row: int, col: int, value) -> None:
        self._wb.Sheets(sheet_name).Cells(row, col).Value = value

    def count_a(self, sheet_name: str, row: int) -> int:
        """指定行の空でないセル数を返す（空行判定に使用）。"""
        ws = self._wb.Sheets(sheet_name)
        return self._excel.WorksheetFunction.CountA(ws.Rows(row))

    def used_last_row(self, sheet_name: str) -> int:
        ws = self._wb.Sheets(sheet_name)
        return ws.UsedRange.Row + ws.UsedRange.Rows.Count - 1

    def read_rows(self, sheet_name: str, min_row: int = 2) -> list[tuple]:
        """指定シートの行データをタプルのリストで返す。"""
        ws = self._wb.Sheets(sheet_name)
        last_row = self.used_last_row(sheet_name)
        last_col = ws.UsedRange.Column + ws.UsedRange.Columns.Count - 1
        return [
            tuple(ws.Cells(row, col).Value for col in range(1, last_col + 1))
            for row in range(min_row, last_row + 1)
        ]

    def read_rows_as_dicts(self, sheet_name: str, header_row: int = 1) -> list[dict]:
        """ヘッダー行をキーとした辞書のリストで返す。"""
        ws = self._wb.Sheets(sheet_name)
        last_row = self.used_last_row(sheet_name)
        last_col = ws.UsedRange.Column + ws.UsedRange.Columns.Count - 1
        headers = [ws.Cells(header_row, col).Value for col in range(1, last_col + 1)]
        return [
            dict(zip(headers, (ws.Cells(row, col).Value for col in range(1, last_col + 1))))
            for row in range(header_row + 1, last_row + 1)
        ]

    def run_macro(self, macro_name: str) -> None:
        """VBA マクロを実行する。"""
        self._excel.Run(macro_name)

    def save_as(self, path: str, read_pw: str = "", write_pw: str = "") -> None:
        self._wb.SaveAs(path, Password=read_pw, WriteResPassword=write_pw)

    def close(self) -> None:
        if self._wb:
            self._wb.Close(SaveChanges=False)
        if self._excel:
            self._excel.Quit()


class WindowHandler:
    """ウィンドウ操作クラス。"""

    def __init__(self, title: str) -> None:
        self._hwnd = win32gui.FindWindow(None, title)
        if self._hwnd == 0:
            raise RuntimeError(f"ウィンドウが見つかりません: {title}")

    def activate(self) -> None:
        win32gui.ShowWindow(self._hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(self._hwnd)

    def get_title(self) -> str:
        return win32gui.GetWindowText(self._hwnd)


class RegistryHandler:
    """レジストリ操作クラス。"""

    def __init__(self, hive: int, key_path: str) -> None:
        self._key = win32api.RegOpenKey(hive, key_path)

    def __enter__(self) -> "RegistryHandler":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def read(self, value_name: str) -> str:
        value, _ = win32api.RegQueryValueEx(self._key, value_name)
        return value

    def close(self) -> None:
        win32api.RegCloseKey(self._key)
