"""SalesforceApiClient のテスト。

実際の Salesforce には接続せず、レスポンスの解釈・リクエストの組み立てなど
純粋なロジック部分をテストする（通信部分は実機で確認する）。
"""

import pytest

from comken.exceptions import SalesforceError
from comken.salesforce import api as requests_api

IMPLEMENTATIONS = pytest.mark.parametrize("api", [requests_api], ids=["requests"])


class _FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class TestClientCredentialsLogin:
    """OAuth 2.0 クライアントクレデンシャルフローの認証テスト。"""

    def test_login_obtains_access_token(self, monkeypatch):
        """トークン応答から access_token と instance_url を取り出せることを確認する。"""
        captured = {}

        def fake_post(self, url, data=None, **kwargs):
            captured["url"] = url
            captured["data"] = data
            return _FakeResponse(
                payload={
                    "access_token": "TOKEN123",
                    "instance_url": "https://example.my.salesforce.com",
                }
            )

        monkeypatch.setattr("requests.Session.post", fake_post)

        sf = requests_api.SalesforceApiClient(
            "cid", "csecret", "https://example.my.salesforce.com"
        )

        assert sf._access_token == "TOKEN123"
        assert sf._instance_url == "https://example.my.salesforce.com"
        assert captured["url"].endswith("/services/oauth2/token")
        assert captured["data"]["grant_type"] == "client_credentials"
        assert captured["data"]["client_id"] == "cid"

    def test_login_failure_raises(self, monkeypatch):
        """認証失敗（4xx）は対処法つきの SalesforceError になることを確認する。"""
        monkeypatch.setattr(
            "requests.Session.post",
            lambda self, url, **kw: _FakeResponse(status_code=400, text="invalid_client"),
        )

        with pytest.raises(SalesforceError, match="認証に失敗"):
            requests_api.SalesforceApiClient("cid", "bad", "https://example.my.salesforce.com")


@IMPLEMENTATIONS
class TestCsvHelpers:
    def test_dicts_to_csv_roundtrip(self, api):
        """辞書 → CSV → 辞書 の往復で値が保たれることを確認する。"""
        records = [
            {"Name": "取引先A", "AnnualRevenue": "1000"},
            {"Name": "取引先, カンマ入り", "AnnualRevenue": "2000"},
        ]

        assert api._csv_to_dicts(api._dicts_to_csv(records)) == records


def _make_client(api):
    """ログインを通さずにクライアントを作る（ロジックのテスト用）。"""
    client = api.SalesforceApiClient.__new__(api.SalesforceApiClient)
    client._access_token = "TOKEN123"
    client._instance_url = "https://example.my.salesforce.com"
    return client


@IMPLEMENTATIONS
class TestQueryPagination:
    def test_follows_next_records_url(self, api, monkeypatch):
        """done になるまで nextRecordsUrl を辿って全件返すことを確認する。"""
        client = _make_client(api)
        pages = {
            "1ページ目": (
                {
                    "records": [{"attributes": {}, "Name": "A"}],
                    "done": False,
                    "nextRecordsUrl": "/next",
                },
                {},
            ),
            "/next": ({"records": [{"attributes": {}, "Name": "B"}], "done": True}, {}),
        }
        calls = []

        def fake_request(method, path, **kwargs):
            calls.append(path)
            return pages["/next"] if path == "/next" else pages["1ページ目"]

        monkeypatch.setattr(client, "_request", fake_request)

        records = client.query("SELECT Name FROM Account")

        assert records == [{"Name": "A"}, {"Name": "B"}]  # attributes は除かれる
        assert len(calls) == 2


@IMPLEMENTATIONS
class TestUpsert:
    def test_builds_external_id_path(self, api, monkeypatch):
        """外部IDがURLパスに入り、ボディからは除かれることを確認する。"""
        client = _make_client(api)
        captured = {}

        def fake_request(method, path, body=None, **kwargs):
            captured.update(method=method, path=path, body=body)
            return None, {}

        monkeypatch.setattr(client, "_request", fake_request)

        client.upsert("Account", "ExternalId__c", {"ExternalId__c": "001", "Name": "取引先"})

        assert captured["method"] == "PATCH"
        assert captured["path"].endswith("/sobjects/Account/ExternalId__c/001")
        assert captured["body"] == {"Name": "取引先"}
