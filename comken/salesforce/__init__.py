"""
salesforce — Salesforce API クライアント

    from comken.salesforce import SalesforceApiClient

認証は OAuth 2.0 クライアントクレデンシャルフロー（client_id / client_secret）。
ユーザー名・パスワード・セキュリティトークンは使わない。

| クラス | 依存 | 用途 |
|---|---|---|
| SalesforceApiClient（推奨） | requests | CRUD・SOQL・レポート・Bulk 2.0 |
| SalesforceRestClient | requests | REST API 直接操作（低レベル） |
| SalesforceReportClient | requests | レポート取得（低レベル） |
"""

from .api import SalesforceApiClient
from .report import SalesforceReportClient
from .rest_api import SalesforceRestClient

__all__ = ["SalesforceApiClient", "SalesforceRestClient", "SalesforceReportClient"]
