"""
salesforce/simple_sf.py — Salesforce CRUD クライアント（simple-salesforce ベース）

simple-salesforce ライブラリを使って Salesforce のレコード操作を行う。
SOQL クエリ、レコードの作成・更新・削除・Upsert に対応する。

レポートの取得は src/salesforce/report.py の SalesforceReportClient を使うこと。
REST API を直接叩く場合は src/salesforce/rest_api.py の SalesforceRestClient を使うこと。

使い方:
    from src.salesforce.simple_sf import SalesforceClient

    sf = SalesforceClient(
        username="user@example.com",
        password="password",
        security_token="セキュリティトークン",
    )

    records = sf.query("SELECT Id, Name FROM Account")
    new_id  = sf.insert("Account", {"Name": "新規取引先"})
    sf.update("Account", record_id=new_id, data={"Name": "更新後の名前"})
    sf.delete("Account", record_id=new_id)
"""

from simple_salesforce import Salesforce


class SalesforceClient:
    """simple-salesforce を使った Salesforce 接続クライアント。

    使い方:
        sf = SalesforceClient(
            username="user@example.com",
            password="password",
            security_token="セキュリティトークン",
        )

        # レコード取得（全件。ページネーション自動）
        records = sf.query("SELECT Id, Name FROM Account WHERE IsDeleted = false")
        # → [{"Id": "001...", "Name": "取引先A", ...}, ...]

        # レコード作成（作成された Id を返す）
        new_id = sf.insert("Account", {"Name": "新規取引先"})

        # レコード更新
        sf.update("Account", record_id=new_id, data={"Name": "更新後の名前"})

        # 外部 ID で Upsert（一致すれば更新、なければ作成）
        sf.upsert("Account", external_id_field="ExternalId__c", data={
            "ExternalId__c": "001",
            "Name": "取引先",
        })

        # レコード削除
        sf.delete("Account", record_id=new_id)
    """

    def __init__(
        self,
        username: str,
        password: str,
        security_token: str,
        domain: str = "login",
    ) -> None:
        """
        Args:
            username: Salesforce のログインユーザー名（メールアドレス形式）。
            password: パスワード。
            security_token: セキュリティトークン（プロフィール設定から取得）。
            domain: 接続先ドメイン。本番環境は "login"、Sandbox は "test"。
        """
        self._sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain,
        )

    def query(self, soql: str) -> list[dict]:
        """SOQL クエリを実行してレコードを返す（全件取得・ページネーション自動）。

        Args:
            soql: 実行する SOQL クエリ文字列。

        Returns:
            レコードの辞書のリスト。
        """
        result = self._sf.query_all(soql)
        return result["records"]

    def insert(self, object_name: str, data: dict) -> str:
        """レコードを作成して Id を返す。

        Args:
            object_name: オブジェクト API 名（例: "Account", "Contact", "CustomObj__c"）。
            data: 作成するレコードのフィールド値の辞書。

        Returns:
            作成されたレコードの Id。
        """
        result = getattr(self._sf, object_name).create(data)
        return result["id"]

    def update(self, object_name: str, record_id: str, data: dict) -> None:
        """レコードを更新する。

        Args:
            object_name: オブジェクト API 名。
            record_id: 更新するレコードの Id。
            data: 更新するフィールド値の辞書。
        """
        getattr(self._sf, object_name).update(record_id, data)

    def delete(self, object_name: str, record_id: str) -> None:
        """レコードを削除する。

        Args:
            object_name: オブジェクト API 名。
            record_id: 削除するレコードの Id。
        """
        getattr(self._sf, object_name).delete(record_id)

    def upsert(self, object_name: str, external_id_field: str, data: dict) -> None:
        """外部 ID を使って Upsert する（一致すれば更新、なければ作成）。

        Args:
            object_name: オブジェクト API 名。
            external_id_field: 外部 ID フィールドの API 名（例: "ExternalId__c"）。
            data: フィールド値の辞書。external_id_field の値を含む必要がある。
        """
        getattr(self._sf, object_name).upsert(
            f"{external_id_field}/{data[external_id_field]}", data
        )
