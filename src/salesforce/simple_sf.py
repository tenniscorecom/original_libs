from simple_salesforce import Salesforce


class SalesforceClient:
    """simple-salesforce を使った Salesforce 接続クライアント。"""

    def __init__(self, username: str, password: str, security_token: str, domain: str = "login") -> None:
        self._sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain,
        )

    def query(self, soql: str) -> list[dict]:
        result = self._sf.query_all(soql)
        return result["records"]

    def insert(self, object_name: str, data: dict) -> str:
        """レコードを作成して Id を返す。"""
        result = getattr(self._sf, object_name).create(data)
        return result["id"]

    def update(self, object_name: str, record_id: str, data: dict) -> None:
        getattr(self._sf, object_name).update(record_id, data)

    def delete(self, object_name: str, record_id: str) -> None:
        getattr(self._sf, object_name).delete(record_id)

    def upsert(self, object_name: str, external_id_field: str, data: dict) -> None:
        getattr(self._sf, object_name).upsert(f"{external_id_field}/{data[external_id_field]}", data)
