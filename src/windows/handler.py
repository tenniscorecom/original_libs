import win32com.client
import win32gui
import win32con
import pywintypes


def open_excel_com(path: str, password: str = "") -> tuple:
    """Excel ファイルを COM で開く。数式の計算結果を読む場合に使用する。"""
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    kwargs = {"Filename": path}
    if password:
        kwargs["Password"] = password
    wb = excel.Workbooks.Open(**kwargs)
    excel.CalculateFull()
    return excel, wb


def save_excel_com(wb, path: str, read_pw: str = "", write_pw: str = "") -> None:
    """パスワードをかけて Excel ファイルを保存する。"""
    wb.SaveAs(path, Password=read_pw, WriteResPassword=write_pw)


def close_excel_com(excel, wb) -> None:
    if wb:
        wb.Close(SaveChanges=False)
    if excel:
        excel.Quit()


def find_window(title: str) -> int:
    hwnd = win32gui.FindWindow(None, title)
    if hwnd == 0:
        raise RuntimeError(f"ウィンドウが見つかりません: {title}")
    return hwnd


def activate_window(hwnd: int) -> None:
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)


def read_registry(hive: int, key_path: str, value_name: str) -> str:
    import win32api
    key = win32api.RegOpenKey(hive, key_path)
    try:
        value, _ = win32api.RegQueryValueEx(key, value_name)
        return value
    finally:
        win32api.RegCloseKey(key)
