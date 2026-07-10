"""
windows/handler.py — Windows API ユーティリティ（pywin32）

pywin32 を使った Windows 固有操作を提供する。

- ExcelComHandler: 数式の計算結果を読む、VBA マクロを実行する、パスワード付き保存など
- WindowHandler: ウィンドウの検索・前面表示
- RegistryHandler: レジストリ値の読み取り

通常の Excel 読み書きは src/excel/handler.py の ExcelFile（openpyxl）を使うこと。
ExcelComHandler は数式やマクロが必要な場面に限定して使う。
"""

import win32api
import win32com.client
import win32con
import win32gui
import pywintypes
from pathlib import Path


class ExcelComHandler:
    """win32com を使った Excel 操作クラス。

    openpyxl では対応できない以下の操作に使う:
        - 数式の計算結果を読む（CalculateFull で再計算してから取得）
        - VBA マクロを実行する
        - パスワード付きで保存する

    使い方:
        with ExcelComHandler("data.xlsx") as h:
            # 数式の計算結果を取得
            value = h.read_cell("Sheet1", row=2, col=3)

            # 行データをまとめて取得
            rows = h.read_rows("Sheet1")
            rows = h.read_rows_as_dicts("Sheet1")

            # 最終行を取得
            last_row = h.used_last_row("Sheet1")

            # 行全体が空かどうか確認
            if h.count_a("Sheet1", row=5) == 0:
                print("5行目は空行")

            # マクロを実行
            h.run_macro("Module1.UpdateData")

            # パスワードをかけて保存
            h.save_as("output.xlsx", read_pw="読み取りPW", write_pw="書き込みPW")
    """

    def __init__(self, path: str | Path, password: str = "") -> None:
        """
        Args:
            path: Excel ファイルのパス。
            password: 読み取りパスワード（パスワード保護されたファイルを開く場合）。
        """
        self._excel = win32com.client.Dispatch("Excel.Application")
        self._excel.Visible = False
        self._excel.DisplayAlerts = False
        kwargs = {"Filename": str(Path(path).resolve())}
        if password:
            kwargs["Password"] = password
        self._wb = self._excel.Workbooks.Open(**kwargs)
        self._excel.CalculateFull()

    def __enter__(self) -> "ExcelComHandler":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def sheet(self, name: str):
        """シートオブジェクトを返す。"""
        return self._wb.Sheets(name)

    def read_cell(self, sheet_name: str, row: int, col: int):
        """セルの値を返す（数式の計算結果）。

        Args:
            sheet_name: シート名。
            row: 行番号（1始まり）。
            col: 列番号（1始まり。A列=1、B列=2、…）。
        """
        return self._wb.Sheets(sheet_name).Cells(row, col).Value

    def write_cell(self, sheet_name: str, row: int, col: int, value) -> None:
        """セルに値を書き込む。

        Args:
            sheet_name: シート名。
            row: 行番号（1始まり）。
            col: 列番号（1始まり）。
            value: 書き込む値。
        """
        self._wb.Sheets(sheet_name).Cells(row, col).Value = value

    def read_rows(self, sheet_name: str, min_row: int = 2) -> list[tuple]:
        """指定シートの行データをタプルのリストで返す。

        Args:
            sheet_name: シート名。
            min_row: 読み始める行番号（デフォルト: 2 でヘッダーをスキップ）。

        Returns:
            各行を値のタプルにしたリスト。
        """
        ws = self._wb.Sheets(sheet_name)
        last_row = self.used_last_row(sheet_name)
        last_col = ws.UsedRange.Column + ws.UsedRange.Columns.Count - 1
        return [
            tuple(ws.Cells(row, col).Value for col in range(1, last_col + 1))
            for row in range(min_row, last_row + 1)
        ]

    def read_rows_as_dicts(self, sheet_name: str, header_row: int = 1) -> list[dict]:
        """ヘッダー行をキーとした辞書のリストで返す。

        Args:
            sheet_name: シート名。
            header_row: ヘッダーが存在する行番号（デフォルト: 1）。

        Returns:
            [{"列名": 値, ...}, ...] の形式のリスト。
        """
        ws = self._wb.Sheets(sheet_name)
        last_row = self.used_last_row(sheet_name)
        last_col = ws.UsedRange.Column + ws.UsedRange.Columns.Count - 1
        headers = [ws.Cells(header_row, col).Value for col in range(1, last_col + 1)]
        return [
            dict(zip(headers, (ws.Cells(row, col).Value for col in range(1, last_col + 1))))
            for row in range(header_row + 1, last_row + 1)
        ]

    def count_a(self, sheet_name: str, row: int) -> int:
        """指定行の空でないセル数を返す。

        数式が入っていても "" を返すセルは空としてカウントされる。
        行全体が空かどうかの判定（スキップ処理）に使う。

        Args:
            sheet_name: シート名。
            row: 確認する行番号。

        Returns:
            空でないセルの数。0 なら行全体が空。
        """
        ws = self._wb.Sheets(sheet_name)
        return self._excel.WorksheetFunction.CountA(ws.Rows(row))

    def used_last_row(self, sheet_name: str) -> int:
        """データが存在する最終行の行番号を返す。

        UsedRange を使うため、数式が入ったセルも含めて正確に最終行を取得できる。

        Args:
            sheet_name: シート名。

        Returns:
            最終行の行番号（1始まり）。
        """
        ws = self._wb.Sheets(sheet_name)
        return ws.UsedRange.Row + ws.UsedRange.Rows.Count - 1

    def run_macro(self, macro_name: str) -> None:
        """VBA マクロを実行する。

        Args:
            macro_name: 実行するマクロ名。"モジュール名.プロシージャ名" の形式で指定する。
                        例: "Module1.UpdateData"
        """
        self._excel.Run(macro_name)

    def save_as(self, path: str | Path, read_pw: str = "", write_pw: str = "") -> None:
        """ファイルを別名で保存する。パスワードを設定できる。

        Args:
            path: 保存先のパス。
            read_pw: 読み取りパスワード（省略可）。
            write_pw: 書き込みパスワード（省略可）。
        """
        self._wb.SaveAs(str(Path(path).resolve()), Password=read_pw, WriteResPassword=write_pw)

    def close(self) -> None:
        """Excel を閉じる。with 文を使う場合は自動で呼ばれる。"""
        if self._wb:
            self._wb.Close(SaveChanges=False)
        if self._excel:
            self._excel.Quit()


class WindowHandler:
    """ウィンドウの検索・操作クラス。

    タイトルでウィンドウを検索し、前面に表示する。

    使い方:
        w = WindowHandler("メモ帳")
        w.activate()        # ウィンドウを前面に表示
        w.get_title()       # ウィンドウタイトルを取得
    """

    def __init__(self, title: str) -> None:
        """
        Args:
            title: 検索するウィンドウのタイトル（完全一致）。

        Raises:
            RuntimeError: ウィンドウが見つからない場合。
        """
        self._hwnd = win32gui.FindWindow(None, title)
        if self._hwnd == 0:
            raise RuntimeError(f"ウィンドウが見つかりません: {title}")

    def activate(self) -> None:
        """ウィンドウを前面に表示する。最小化されている場合は復元する。"""
        win32gui.ShowWindow(self._hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(self._hwnd)

    def get_title(self) -> str:
        """ウィンドウのタイトルを返す。"""
        return win32gui.GetWindowText(self._hwnd)


class RegistryHandler:
    """レジストリ値の読み取りクラス。with 文で確実にキーを閉じる。

    使い方:
        import win32con
        from src.windows.handler import RegistryHandler

        with RegistryHandler(win32con.HKEY_CURRENT_USER, r"Software\\MyApp") as r:
            value = r.read("SettingName")
            print(value)
    """

    def __init__(self, hive: int, key_path: str) -> None:
        """
        Args:
            hive: レジストリのルートキー（例: win32con.HKEY_CURRENT_USER）。
            key_path: キーのパス（例: r"Software\\MyApp"）。
        """
        self._key = win32api.RegOpenKey(hive, key_path)

    def __enter__(self) -> "RegistryHandler":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def read(self, value_name: str) -> str:
        """レジストリ値を読み取る。

        Args:
            value_name: 読み取る値の名前。

        Returns:
            レジストリ値の文字列。
        """
        value, _ = win32api.RegQueryValueEx(self._key, value_name)
        return value

    def close(self) -> None:
        """レジストリキーを閉じる。with 文を使う場合は自動で呼ばれる。"""
        win32api.RegCloseKey(self._key)
