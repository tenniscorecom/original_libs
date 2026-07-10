import requests


class SalesforceRestClient:
    """Salesforce REST API を直接叩くクライアント。"""

    def __init__(self, instance_url: str, access_token: str) -> None:
        self._base_url = f"{instance_url}/services/data/v59.0"
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    @classmethod
    def from_password(cls, username: str, password: str, security_token: str,
                      client_id: str, client_secret: str, domain: str = "login") -> "SalesforceRestClient":
        """ユーザー名・パスワードで認証してインスタンスを返す。"""
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
        resp = requests.post(f"{self._base_url}/sobjects/{object_name}", headers=self._headers, json=data)
        resp.raise_for_status()
        return resp.json()["id"]

    def update(self, object_name: str, record_id: str, data: dict) -> None:
        resp = requests.patch(f"{self._base_url}/sobjects/{object_name}/{record_id}", headers=self._headers, json=data)
        resp.raise_for_status()

    def delete(self, object_name: str, record_id: str) -> None:
        resp = requests.delete(f"{self._base_url}/sobjects/{object_name}/{record_id}", headers=self._headers)
        resp.raise_for_status()
