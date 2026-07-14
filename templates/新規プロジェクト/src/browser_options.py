"""
src/browser_options.py — このプロジェクトのブラウザ設定

comken の BrowserOptions のデフォルトから、変えたい項目だけ上書きする。
ブラウザ設定は「環境で変わる非機密の値」ではなく「コードの一部」なので、
config.ini ではなくこのファイル（src/ 内の Python）で持つ。

ブラウザ操作を使わないプロジェクトでは、このファイルは削除してよい。

使い方（呼ぶ側）:
    from comken.browser import EdgeDriver

    from .browser_options import options

    with EdgeDriver(options) as d:
        d.open("https://example.com")
        ...
"""

from comken.browser.options import BrowserOptions

options = BrowserOptions()
# 変えたい項目だけ上書きする（設定できる項目の一覧は comken.browser.options を参照）
# options.HEADLESS = True                      # 画面を出さずに動かす
# options.DOWNLOAD_DIR = r"C:\作業\downloads"   # ダウンロード先（ローカルにする）
# options.WAIT_SECONDS = 20                     # 要素待機のタイムアウト秒
