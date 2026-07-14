"""
サンプル: Salesforce のデータを Excel に出力する

SOQL でレコードを取得して、そのまま Excel レポートにする定番の流れ。
認証情報の安全な扱い方（credentials + config.ini の [CREDENTIALS]）もこの形で覚える。

※ 実行には Salesforce 環境（本番 or Sandbox）が必要。

事前準備:
    1. Salesforce 側で接続アプリ（Connected App）を用意し、クライアントクレデンシャル
       フローを有効化する（詳細は docs/Salesforce認証パターン.md）
    2. このフォルダの config.ini.example をコピーして config.ini を作り、
       [SALESFORCE] DOMAIN_URL に組織の My Domain を書く
    3. このフォルダで python -m comken.credentials を起動し、
       「まとめて登録」で salesforce_client_id / _client_secret を登録する
       （credentials.py の REQUIRED_CREDENTIALS 宣言が読み取られる）

実行方法:
    リポジトリのルートで python -m examples.salesforce_to_excel.run
"""

import logging

from comken import setup_logger
from comken.credentials import Credentials
from comken.excel import ExcelFile
from comken.salesforce import SalesforceApiClient
from comken.utils import FileNameBuilder

from .config import config

# 取得する内容はコードの一部としてここに書く（環境で変わる値だけを config.ini に置く）
SOQL = "SELECT Id, Name, Phone FROM Account WHERE IsDeleted = false LIMIT 100"
SHEET = "Sheet1"

logger = logging.getLogger(__name__)


def main() -> None:
    # 認証情報は config.ini に書かず、暗号化保存されたものをプレフィックスで取り出す。
    # OAuth 2.0 クライアントクレデンシャル（client_id / client_secret）で認証する
    cred = Credentials(config.CREDENTIALS.SALESFORCE)
    sf = SalesforceApiClient(
        client_id=cred.client_id,
        client_secret=cred.client_secret,
        domain_url=config.SALESFORCE.DOMAIN_URL,  # 組織の My Domain（非機密なので config.ini）
    )

    # SOQL は全件取得（ページネーション自動）。数万件以上なら sf.bulk_query() を使う
    records = sf.query(SOQL)
    logger.info("取得: %d 件", len(records))

    # レポート（画面で作った集計表）をそのまま取りたい場合は SOQL の代わりにこちら:
    # rows = sf.run_report("00O000000000001")  # ID はレポートを開いたときの URL 末尾

    output_path = config.REPORT.OUTPUT_FOLDER / FileNameBuilder("取引先一覧").suffix()
    with ExcelFile.create(output_path) as f:
        s = f.sheet(SHEET)
        s.write_table(records)  # query の結果（辞書のリスト）をそのまま書ける
        s.auto_width()
        s.freeze_header()
        f.save()

    logger.info("出力: %s", output_path)


if __name__ == "__main__":
    setup_logger("main")
    main()
