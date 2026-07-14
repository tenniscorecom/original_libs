"""
src/credentials.py — このプロジェクトが使う認証情報の宣言

REQUIRED_CREDENTIALS に「どのサービスの・どの項目を使うか」を書いておくと、
認証情報の登録.bat（登録 GUI）を開いたときに、未登録の項目が一覧表示される。

- 辞書のキー: config.ini の [CREDENTIALS] に書くキー名（大文字）
- 値のリスト: 使う項目名（username / password / token など）

コードで使う認証情報を増やしたら、この宣言も必ず更新すること
（宣言が実態とズレると「まとめて登録」で項目が漏れる）。

コード側での取り出し方:
    from comken import config
    from comken.credentials import Credentials

    # config.ini の [CREDENTIALS] SALESFORCE で指定したプレフィックスを使う
    sf = Credentials(config.CREDENTIALS.SALESFORCE)
    sf.username   # → salesforce_username の値
    sf.password   # → salesforce_password の値
"""

REQUIRED_CREDENTIALS = {
    # 使うぶんだけ残し、不要な行は消す。使わないプロジェクトなら空 {} でよい
    # "SALESFORCE": ["username", "password", "token"],
    # "OJU_SYS": ["password"],
}
