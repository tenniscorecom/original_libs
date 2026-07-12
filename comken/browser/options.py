"""
BrowserOptions: Edge/Chrome 起動オプションの定義クラス。

- bool 属性: True = 有効、False = 無効
- str 属性: 値付きオプション。None で無効

プロジェクト側でサブクラスを作り、必要な属性だけ上書きする:

    from comken.browser.options import BrowserOptions

    class MyOptions(BrowserOptions):
        INCOGNITO = False
        WINDOW_SIZE = "1600,1024"
"""

from pathlib import Path


class BrowserOptions:
    # ── ドライバー設定 ──
    DRIVER_PATH: str = r"C:\Users\Public\Documents\msedgedriver.exe"
    WAIT_SECONDS: int = 10
    DOWNLOAD_DIR: str | None = None  # None = 一時フォルダを自動作成（EdgeDriver 終了時に削除）

    # 属性名 → 実際の Chrome 引数
    _BOOL_ARGS: dict[str, str] = {
        "DISABLE_AUTOMATION_CONTROLLED": "--disable-blink-features=AutomationControlled",
        "DISABLE_BACKGROUND_NETWORKING": "--disable-background-networking",
        "DISABLE_DEFAULT_APPS": "--disable-default-apps",
        "DISABLE_DEV_SHM_USAGE": "--disable-dev-shm-usage",
        "DISABLE_DOWNLOAD_BUBBLE": "--disable-features=DownloadBubble,DownloadBubbleV2",
        "DISABLE_EXTENSIONS": "--disable-extensions",
        "DISABLE_IMAGES": "--blink-settings=imagesEnabled=false",
        "DISABLE_POPUP_BLOCKING": "--disable-popup-blocking",
        "DISABLE_TRANSLATE": "--disable-features=Translate",
        "HEADLESS": "--headless=new",
        "HIDE_SCROLLBARS": "--hide-scrollbars",
        "IGNORE_CERTIFICATE_ERRORS": "--ignore-certificate-errors",
        "IGNORE_SSL_ERRORS": "--ignore-ssl-errors",
        "INCOGNITO": "--incognito",
        "MUTE_AUDIO": "--mute-audio",
        "NO_DEFAULT_BROWSER_CHECK": "--no-default-browser-check",
        "NO_SANDBOX": "--no-sandbox",
        "START_MAXIMIZED": "--start-maximized",
        "TEST_TYPE_GPU": "--test-type=gpu",
    }

    # 属性名 → 引数テンプレート（{} に値が入る）
    _VALUE_ARGS: dict[str, str] = {
        "USER_AGENT": "--user-agent={}",
        "WINDOW_SIZE": "--window-size={}",
        "WINDOW_POSITION": "--window-position={}",
    }

    # ── デフォルト有効 ──
    DISABLE_AUTOMATION_CONTROLLED: bool = True
    DISABLE_BACKGROUND_NETWORKING: bool = True
    DISABLE_DEFAULT_APPS: bool = True
    DISABLE_DEV_SHM_USAGE: bool = True
    DISABLE_DOWNLOAD_BUBBLE: bool = True
    DISABLE_EXTENSIONS: bool = True
    DISABLE_POPUP_BLOCKING: bool = True
    DISABLE_TRANSLATE: bool = True
    IGNORE_CERTIFICATE_ERRORS: bool = True
    IGNORE_SSL_ERRORS: bool = True
    INCOGNITO: bool = True
    MUTE_AUDIO: bool = True
    NO_DEFAULT_BROWSER_CHECK: bool = True
    NO_SANDBOX: bool = True
    START_MAXIMIZED: bool = True
    TEST_TYPE_GPU: bool = True

    # ── デフォルト無効 ──
    HEADLESS: bool = False
    DISABLE_IMAGES: bool = False
    HIDE_SCROLLBARS: bool = False

    # ── 値付き（None = 無効）──
    USER_AGENT: str | None = None
    WINDOW_SIZE: str | None = None
    WINDOW_POSITION: str | None = None

    def __repr__(self) -> str:
        """print() でデフォルト値一覧を表示する。サブクラスではデフォルトからの差分も表示。"""
        base = BrowserOptions()
        lines = [f"{self.__class__.__name__}:"]

        enabled, disabled = [], []
        for attr, arg in self._BOOL_ARGS.items():
            current = getattr(self, attr, False)
            default = getattr(base, attr, False)
            diff = " *" if current != default else ""
            if current:
                enabled.append(f"    {attr:<35} → {arg}{diff}")
            else:
                disabled.append(f"    {attr:<35}{diff}")

        lines.append("  ── 有効 ──")
        lines.extend(enabled or ["    (なし)"])
        lines.append("  ── 無効 ──")
        lines.extend(disabled or ["    (なし)"])

        lines.append("  ── 値付き ──")
        for attr, template in self._VALUE_ARGS.items():
            value = getattr(self, attr, None)
            default = getattr(base, attr, None)
            diff = " *" if value != default else ""
            display = template.format(value) if value else "None"
            lines.append(f"    {attr:<35} = {display}{diff}")

        lines.append("  ── ドライバー設定 ──")
        for attr in ("DRIVER_PATH", "WAIT_SECONDS", "DOWNLOAD_DIR"):
            current = getattr(self, attr)
            default = getattr(base, attr)
            diff = " *" if current != default else ""
            display = current if current is not None else "None（一時フォルダ自動作成）"
            lines.append(f"    {attr:<35} = {display}{diff}")

        if self.__class__ is not BrowserOptions:
            lines.append("  (* = デフォルトから変更)")

        return "\n".join(lines)

    def build(self) -> list[str]:
        """有効なオプションを Chrome 引数リストに変換する。"""
        args = []

        for attr, arg in self._BOOL_ARGS.items():
            if getattr(self, attr, False):
                args.append(arg)

        for attr, template in self._VALUE_ARGS.items():
            value = getattr(self, attr, None)
            if value:
                args.append(template.format(value))

        return args
