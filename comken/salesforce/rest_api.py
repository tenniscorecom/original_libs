"""
salesforce/rest_api.py — Salesforce REST API クライアント（低レベル）

requests を使って Salesforce REST API を直接叩くクライアント。
ページネーションを自動で処理する。細かい API 制御が必要な場合に使う。
通常は api.py の SalesforceApiClient を優先すること。

認証は OAuth 2.0 クライアントクレデンシャルフロー（client_id / client_secret）。

使い方:
    # クライアントクレデンシャルで認証してインスタンスを作る
    sf = SalesforceRestClient.from_client_credentials(
        client_id="接続アプリの Consumer Key",
        client_secret="接続アプリの Consumer Secret",
        domain_url="https://your-domain.my.salesforce.com",
    )

    # アクセストークンが既にある場合
    sf = SalesforceRestClient(
        instance_url="https://xxx.my.salesforce.com",
        access_token="アクセストークン",
    )
"""

import requests

from ..exceptions import SalesforceError

_API_VERSION = "v60.0"
_TIMEOUT_SECONDS = 60  # HTTP リクエストのタイムアウト


class SalesforceRestClient:
    """Salesforce REST API を直接叩くクライアント。

    使い方:
        sf = SalesforceRestClient.from_client_credentials(
            client_id="Consumer Key",
            client_secret="Consumer Secret",
            domain_url="https://your-domain.my.salesforce.com",
        )

        # SOQL クエリ（2000件超えは自動でページネーション）
        records = sf.query("SELECT Id, Name FROM Account")

        # レコード作成
        new_id = sf.insert("Account", {"Name": "新規取引先"})

        # レコード更新
        sf.update("Account", record_id=new_id, data={"Name": "更新後"})

        # レコード削除
        sf.delete("Account", record_id=new_id)
    """

    def __init__(self, instance_url: str, access_token: str) -> None:
        """
        Args:
            instance_url: Salesforce インスタンス URL（例: "https://xxx.salesforce.com"）。
            access_token: OAuth アクセストークン。
        """
        self._base_url = f"{instance_url}/services/data/{_API_VERSION}"
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    @classmethod
    def from_client_credentials(
        cls,
        client_id: str,
        client_secret: str,
        domain_url: str,
    ) -> "SalesforceRestClient":
        """OAuth 2.0 クライアントクレデンシャルフローで認証してインスタンスを返す。

        Args:
            client_id: 接続アプリケーションの Consumer Key。
            client_secret: 接続アプリケーションの Consumer Secret。
            domain_url: 組織の My Domain の URL（例: "https://foo.my.salesforce.com"）。
                        クライアントクレデンシャルフローは My Domain が必須。

        Returns:
            認証済みの SalesforceRestClient インスタンス。
        """
        url = f"{domain_url.rstrip('/')}/services/oauth2/token"
        try:
            response = requests.post(
                url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                timeout=_TIMEOUT_SECONDS,
            )
        except requests.exceptions.RequestException as e:
            raise SalesforceError(f"Salesforce に接続できませんでした: {url}（詳細: {e}）") from e
        if response.status_code >= 400:
            raise SalesforceError(
                f"Salesforce の認証に失敗しました（HTTP {response.status_code}）: {response.text}"
            )
        data = response.json()
        return cls(data["instance_url"], data["access_token"])

    def query(self, soql: str) -> list[dict]:
        """SOQL クエリを実行してレコードを返す（全件取得・ページネーション自動）。

        Args:
            soql: 実行する SOQL クエリ文字列。

        Returns:
            レコードの辞書のリスト。
        """
        records = []
        url = f"{self._base_url}/query"
        params = {"q": soql}
        while url:
            data = self._request("GET", url, params=params)
            records.extend(data["records"])
            next_url = data.get("nextRecordsUrl")
            url = f"{self._base_url.split('/services')[0]}{next_url}" if next_url else None
            params = {}
        return records

    def insert(self, object_name: str, data: dict) -> str:
        """レコードを作成して Id を返す。

        Args:
            object_name: オブジェクト API 名（例: "Account"）。
            data: 作成するフィールド値の辞書。

        Returns:
            作成されたレコードの Id。
        """
        result = self._request("POST", f"{self._base_url}/sobjects/{object_name}", json=data)
        return result["id"]

    def update(self, object_name: str, record_id: str, data: dict) -> None:
        """レコードを更新する。

        Args:
            object_name: オブジェクト API 名。
            record_id: 更新するレコードの Id。
            data: 更新するフィールド値の辞書。
        """
        self._request("PATCH", f"{self._base_url}/sobjects/{object_name}/{record_id}", json=data)

    def delete(self, object_name: str, record_id: str) -> None:
        """レコードを削除する。

        Args:
            object_name: オブジェクト API 名。
            record_id: 削除するレコードの Id。
        """
        self._request("DELETE", f"{self._base_url}/sobjects/{object_name}/{record_id}")

    def _request(self, method: str, url: str, json: dict | None = None, params: dict | None = None):
        """REST API を呼び、JSON（本文がなければ None）を返す。

        エラーは SalesforceError に変換し、全リクエストにタイムアウトを付ける。
        """
        try:
            resp = requests.request(
                method,
                url,
                headers=self._headers,
                json=json,
                params=params,
                timeout=_TIMEOUT_SECONDS,
            )
        except requests.exceptions.RequestException as e:
            raise SalesforceError(
                f"Salesforce に接続できませんでした: {method} {url}（詳細: {e}）"
            ) from e
        if resp.status_code >= 400:
            raise SalesforceError(
                f"Salesforce API エラー（HTTP {resp.status_code}）: {method} {url}\n{resp.text}"
            )
        return resp.json() if resp.text else None
