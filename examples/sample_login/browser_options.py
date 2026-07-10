from comken.selenium.options import BrowserOptions


class SampleBrowserOptions(BrowserOptions):
    """sample_login 用のブラウザオプション。

    デフォルト（BrowserOptions）から変更したいものだけ上書きする。
    全オプションのデフォルト値は src/selenium/options.py を参照。
    """

    # このサンプルではシークレットモードを使わない
    INCOGNITO = False

    # ウィンドウサイズを固定（--start-maximized と併用不可なので無効化）
    START_MAXIMIZED = False
    WINDOW_SIZE = "1600,1024"
