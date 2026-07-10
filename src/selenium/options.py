"""
Edge/Chrome WebDriver のデフォルト起動引数。

プロジェクト側では browser_options.ini の [options] add / remove で差分だけ指定する。
動的な値（ユーザーエージェントなど）はプロジェクト側の Python コードで add_args に渡す。
"""

DEFAULT_ARGS: tuple[str, ...] = (
    # bot 検知回避（navigator.webdriver = false）
    "--disable-blink-features=AutomationControlled",
    # バックグラウンドのネットワークサービスを無効
    "--disable-background-networking",
    # 拡張機能を無効
    "--disable-extensions",
    # デフォルトアプリのインストールを無効
    "--disable-default-apps",
    # Docker / GCloud のメモリ対策
    "--disable-dev-shm-usage",
    # ダウンロード完了通知をバブルではなく下部表示
    "--disable-features=DownloadBubble",
    "--disable-features=DownloadBubbleV2",
    # 翻訳機能を無効
    "--disable-features=Translate",
    # ポップアップブロックを無効
    "--disable-popup-blocking",
    # SSL 警告を無視
    "--ignore-certificate-errors",
    "--ignore-ssl-errors",
    # シークレットモード
    "--incognito",
    # 音をミュート
    "--mute-audio",
    # 「既定のブラウザとして設定」バナーを非表示
    "--no-default-browser-check",
    # no-sandbox（Linux / 仮想環境向け）
    "--no-sandbox",
    # ウィンドウ最大化
    "--start-maximized",
    # 「Chrome for Testing」バナーを非表示
    "--test-type=gpu",
)
