"""
BrowserOptions: Edge/Chrome 起動オプションの定義クラス。

- bool 属性: True = 有効、False = 無効
- str 属性:  値付きオプション。None で無効

プロジェクト側でサブクラスを作り、必要な属性だけ上書きする:

    from src.selenium.options import BrowserOptions

    class MyOptions(BrowserOptions):
        INCOGNITO = False          # シークレットモードを無効
        WINDOW_SIZE = "1600,1024"  # ウィンドウサイズを指定
"""


class BrowserOptions:

    # ----------------------------------------------------------------- bool
    # 属性名 → 実際の Chrome 引数
    _BOOL_ARGS: dict[str, str] = {
        "DISABLE_AUTOMATION_CONTROLLED": "--disable-blink-features=AutomationControlled",
        "DISABLE_BACKGROUND_NETWORKING": "--disable-background-networking",
        "DISABLE_DEFAULT_APPS":          "--disable-default-apps",
        "DISABLE_DEV_SHM_USAGE":         "--disable-dev-shm-usage",
        "DISABLE_DOWNLOAD_BUBBLE":       "--disable-features=DownloadBubble,DownloadBubbleV2",
        "DISABLE_EXTENSIONS":            "--disable-extensions",
        "DISABLE_IMAGES":                "--blink-settings=imagesEnabled=false",
        "DISABLE_POPUP_BLOCKING":        "--disable-popup-blocking",
        "DISABLE_TRANSLATE":             "--disable-features=Translate",
        "HEADLESS":                      "--headless=new",
        "HIDE_SCROLLBARS":               "--hide-scrollbars",
        "IGNORE_CERTIFICATE_ERRORS":     "--ignore-certificate-errors",
        "IGNORE_SSL_ERRORS":             "--ignore-ssl-errors",
        "INCOGNITO":                     "--incognito",
        "MUTE_AUDIO":                    "--mute-audio",
        "NO_DEFAULT_BROWSER_CHECK":      "--no-default-browser-check",
        "NO_SANDBOX":                    "--no-sandbox",
        "START_MAXIMIZED":               "--start-maximized",
        "TEST_TYPE_GPU":                 "--test-type=gpu",
    }

    # ----------------------------------------------------------------- str
    # 属性名 → 引数テンプレート（{} に値が入る）
    _VALUE_ARGS: dict[str, str] = {
        "USER_AGENT":      "--user-agent={}",
        "WINDOW_SIZE":     "--window-size={}",
        "WINDOW_POSITION": "--window-position={}",
    }

    # ============================================================ デフォルト有効
    DISABLE_AUTOMATION_CONTROLLED: bool = True
    DISABLE_BACKGROUND_NETWORKING: bool = True
    DISABLE_DEFAULT_APPS:          bool = True
    DISABLE_DEV_SHM_USAGE:         bool = True
    DISABLE_DOWNLOAD_BUBBLE:       bool = True
    DISABLE_EXTENSIONS:            bool = True
    DISABLE_POPUP_BLOCKING:        bool = True
    DISABLE_TRANSLATE:             bool = True
    IGNORE_CERTIFICATE_ERRORS:     bool = True
    IGNORE_SSL_ERRORS:             bool = True
    INCOGNITO:                     bool = True
    MUTE_AUDIO:                    bool = True
    NO_DEFAULT_BROWSER_CHECK:      bool = True
    NO_SANDBOX:                    bool = True
    START_MAXIMIZED:               bool = True
    TEST_TYPE_GPU:                 bool = True

    # ============================================================ デフォルト無効
    HEADLESS:       bool = False
    DISABLE_IMAGES: bool = False
    HIDE_SCROLLBARS: bool = False

    # ============================================================ 値付き（None = 無効）
    USER_AGENT:      str | None = None
    WINDOW_SIZE:     str | None = None
    WINDOW_POSITION: str | None = None

    # ================================================================ build
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
