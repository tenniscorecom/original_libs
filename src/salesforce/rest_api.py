"""
salesforce/rest_api.py — Salesforce REST API クライアント

requests を使って Salesforce REST API を直接叩くクライアント。
ページネーションを自動で処理する。

simple-salesforce が使えない環境や、細かい API 制御が必要な場合に使う。
通常は src/salesforce/simple_sf.py の SalesforceClient を優先すること。

使い方:
    # パスワード認証でインスタンスを作る
    sf = SalesforceRestClient.from_password(
        username="user@example.com",
        password="password",
        security_token="トークン",
        client_id="接続アプリのクライアントID",
        client_secret="接続アプリのクライアントシークレット",
    )

    # アクセストークンが既にある場合
    sf = SalesforceRestClient(
        instance_url="https://xxx.salesforce.com",
        access_token="アクセストークン",
    )
"""

import requests


class SalesforceRestClient:
    """Salesforce REST API を直接叩くクライアント。

    使い方:
        # パスワード認証
        sf = SalesforceRestClient.from_password(
            username="user@example.com",
            password="password",
            security_token="トークン",
            client_id="クライアントID",
            client_secret="クライアントシークレット",
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
        self._base_url = f"{instance_url}/services/data/v59.0"
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    @classmethod
    def from_password(
        cls,
        username: str,
        password: str,
        security_token: str,
        client_id: str,
        client_secret: str,
        domain: str = "login",
    ) -> "SalesforceRestClient":
        """ユーザー名・パスワードで OAuth 認証してインスタンスを返す。

        Args:
            username: Salesforce ログインユーザー名。
            password: パスワード。
            security_token: セキュリティトークン。
            client_id: 接続アプリケーションのクライアント ID。
            client_secret: 接続アプリケーションのクライアントシークレット。
            domain: 接続先ドメイン。本番環境は "login"、Sandbox は "test"。

        Returns:
            認証済みの SalesforceRestClient インスタンス。
        """
        url = f"https://{domain}.salesforce.com/services/oauth2/token"
        response = requests.post(url, data={
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password + security_token,
        })
        response.raise_for_status()
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
            resp = requests.get(url, headers=self._headers, params=params)
            resp.raise_for_status()
            data = resp.json()
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
        resp = requests.post(
            f"{self._base_url}/sobjects/{object_name}",
            headers=self._headers,
            json=data,
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def update(self, object_name: str, record_id: str, data: dict) -> None:
        """レコードを更新する。

        Args:
            object_name: オブジェクト API 名。
            record_id: 更新するレコードの Id。
            data: 更新するフィールド値の辞書。
        """
        resp = requests.patch(
            f"{self._base_url}/sobjects/{object_name}/{record_id}",
            headers=self._headers,
            json=data,
        )
        resp.raise_for_status()

    def delete(self, object_name: str, record_id: str) -> None:
        """レコードを削除する。

        Args:
            object_name: オブジェクト API 名。
            record_id: 削除するレコードの Id。
        """
        resp = requests.delete(
            f"{self._base_url}/sobjects/{object_name}/{record_id}",
            headers=self._headers,
        )
        resp.raise_for_status()
