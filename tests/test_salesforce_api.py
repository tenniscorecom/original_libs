"""SalesforceApiClient のテスト。

実際の Salesforce には接続せず、レスポンスの解釈・リクエストの組み立てなど
純粋なロジック部分をテストする（通信部分は実機で確認する）。
"""

import pytest

from comken.exceptions import SalesforceError
from comken.salesforce_requests import api as requests_api

IMPLEMENTATIONS = pytest.mark.parametrize("api", [requests_api], ids=["requests"])

LOGIN_OK_XML = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns="urn:partner.soap.sforce.com">
  <soapenv:Body>
    <loginResponse>
      <result>
        <serverUrl>https://example.my.salesforce.com/services/Soap/u/60.0/00D123</serverUrl>
        <sessionId>SESSION123</sessionId>
      </result>
    </loginResponse>
  </soapenv:Body>
</soapenv:Envelope>"""

LOGIN_FAIL_XML = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <soapenv:Fault>
      <faultcode>INVALID_LOGIN</faultcode>
      <faultstring>INVALID_LOGIN: Invalid username, password, security token</faultstring>
    </soapenv:Fault>
  </soapenv:Body>
</soapenv:Envelope>"""


@IMPLEMENTATIONS
class TestParseLoginResponse:
    def test_extracts_session_and_instance_url(self, api):
        """成功レスポンスからセッションIDとインスタンスURLを取り出せることを確認する。"""
        session_id, instance_url = api._parse_login_response(LOGIN_OK_XML)

        assert session_id == "SESSION123"
        assert instance_url == "https://example.my.salesforce.com"

    def test_raises_on_login_fault(self, api):
        """ログイン失敗のレスポンスは対処法つきの SalesforceError になることを確認する。"""
        with pytest.raises(SalesforceError, match="INVALID_LOGIN"):
            api._parse_login_response(LOGIN_FAIL_XML)


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
    client._session_id = "SESSION123"
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


class TestOldImportPath:
    """旧 import パス（comken.salesforce）の互換シムのテスト。"""

    def test_old_import_warns_and_returns_client(self):
        """旧パスからの import は FutureWarning 付きで動くことを確認する。"""
        import comken.salesforce

        with pytest.warns(FutureWarning, match="salesforce"):
            cls = comken.salesforce.SalesforceApiClient

        assert cls is requests_api.SalesforceApiClient
