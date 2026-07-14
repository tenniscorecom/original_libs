"""
credentials.py — このサンプルが使う認証情報の宣言

python -m comken.credentials（または --gui）をこのフォルダで起動すると、
この宣言が読み取られて「まとめて登録」メニューに未登録の項目が並ぶ。
キー名を1文字も打たずに登録できるので、スペルミスの余地がない。

コードで使う項目を増やしたら、この宣言も必ず更新する。
"""

# キーは config.ini [CREDENTIALS] のキー名。プレフィックス（値）は config.ini 側で切り替える。
# OAuth 2.0 クライアントクレデンシャル: client_id / client_secret だけを機密として登録する
# （My Domain の URL は非機密なので config.ini の [SALESFORCE] DOMAIN_URL に書く）
REQUIRED_CREDENTIALS = {
    "SALESFORCE": ["client_id", "client_secret"],
}
