"""
salesforce/bulk.py — Salesforce 一括操作クライアント（Bulk API）

大量レコードの一括 insert / update / upsert / delete に対応する。
通常の CRUD（数百件まで）は simple_sf.py の SalesforceClient を使うこと。
1000件を超える場合にこのクライアントを使うと大幅に高速化できる。

使い方:
    from comken.salesforce.bulk import SalesforceBulkClient

    sf = SalesforceBulkClient(
        username="user@example.com",
        password="password",
        security_token="セキュリティトークン",
    )

    rows = [{"Name": "取引先A"}, {"Name": "取引先B"}, ...]

    sf.bulk_insert("Account", rows)
    sf.bulk_update("Account", rows)   # rows に "Id" キーが必要
    sf.bulk_delete("Account", rows)   # rows に "Id" キーが必要
    sf.bulk_upsert("Account", rows, external_id_field="ExternalId__c")
"""

from simple_salesforce import Salesforce


class SalesforceBulkClient:
    """Salesforce Bulk API を使った大量レコード操作クライアント。

    simple-salesforce の Bulk API ラッパーを使用する。
    1ジョブあたり 1万件以上を処理する場合に通常の API より大幅に高速。

    使い方:
        sf = SalesforceBulkClient(
            username="user@example.com",
            password="password",
            security_token="セキュリティトークン",
            # domain="test"  # Sandbox の場合
        )

        rows = [{"Name": f"取引先{i}"} for i in range(10000)]
        results = sf.bulk_insert("Account", rows)
    """

    def __init__(
        self,
        username: str,
        password: str,
        security_token: str,
        domain: str | None = None,
    ) -> None:
        """
        Args:
            username: Salesforce のユーザー名（メールアドレス）。
            password: パスワード。
            security_token: セキュリティトークン。
            domain: "test" を指定すると Sandbox に接続する。本番環境は None（デフォルト）。
        """
        self._sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain,
        )

    def bulk_insert(self, sobject: str, records: list[dict]) -> list[dict]:
        """レコードを一括 insert する。

        records に "Id" を含めないこと（Salesforce 側で自動採番される）。

        Args:
            sobject: オブジェクト名（例: "Account", "Contact"）。
            records: 挿入するレコードのリスト。

        Returns:
            各レコードの結果リスト（{"id": ..., "success": True, ...}）。
        """
        return getattr(self._sf.bulk, sobject).insert(records)

    def bulk_update(self, sobject: str, records: list[dict]) -> list[dict]:
        """レコードを一括 update する。

        各レコードに "Id" キーが必要。

        Args:
            sobject: オブジェクト名。
            records: 更新するレコードのリスト。"Id" キーを含めること。

        Returns:
            各レコードの結果リスト。
        """
        return getattr(self._sf.bulk, sobject).update(records)

    def bulk_upsert(
        self,
        sobject: str,
        records: list[dict],
        external_id_field: str,
    ) -> list[dict]:
        """外部 ID を使って一括 upsert する（存在すれば update、なければ insert）。

        Args:
            sobject: オブジェクト名。
            records: upsert するレコードのリスト。external_id_field の値を含めること。
            external_id_field: 外部 ID フィールドの API 名（例: "ExternalId__c"）。

        Returns:
            各レコードの結果リスト。
        """
        return getattr(self._sf.bulk, sobject).upsert(records, external_id_field)

    def bulk_delete(self, sobject: str, records: list[dict]) -> list[dict]:
        """レコードを一括 delete する。

        各レコードに "Id" キーのみあればよい（他のフィールドは不要）。

        Args:
            sobject: オブジェクト名。
            records: 削除するレコードのリスト。{"Id": "..."} の形式でよい。

        Returns:
            各レコードの結果リスト。
        """
        return getattr(self._sf.bulk, sobject).delete(records)

    def bulk_query(self, soql: str) -> list[dict]:
        """SOQL クエリを Bulk API で実行する（大量レコードの取得に使う）。

        通常の query() は 2000件ごとにページネーションが必要だが、
        bulk_query は全件を一括で取得できる（内部でページネーションを自動処理）。

        Args:
            soql: 実行する SOQL クエリ文字列。

        Returns:
            取得したレコードのリスト。
        """
        return self._sf.bulk.query(soql)
