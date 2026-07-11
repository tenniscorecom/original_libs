"""
salesforce — Salesforce 連携クライアント

推奨は SalesforceApiClient(標準ライブラリのみで動く。追加インストール不要)。

simple-salesforce / requests ベースのクライアントも残しているが、
これらは外部ライブラリの導入承認が下りた環境でのみ使えるため、王道にはしない。

| クラス | 依存 | 用途 |
|---|---|---|
| SalesforceApiClient(推奨) | なし(標準ライブラリのみ) | CRUD・SOQL・レポート・Bulk 2.0 |
| SalesforceClient | simple-salesforce | CRUD・SOQL |
| SalesforceBulkClient | simple-salesforce | Bulk 一括操作 |
| SalesforceRestClient | requests | REST API 直接操作 |
| SalesforceReportClient | requests | レポート取得 |
"""

from .api import SalesforceApiClient

__all__ = ["SalesforceApiClient"]

# 外部ライブラリ版はインストールされている場合だけ使える(未導入でも import エラーにしない)
try:
    from .bulk import SalesforceBulkClient
    from .simple_sf import SalesforceClient

    __all__ += ["SalesforceClient", "SalesforceBulkClient"]
except ImportError:  # simple-salesforce 未導入
    pass

try:
    from .report import SalesforceReportClient
    from .rest_api import SalesforceRestClient

    __all__ += ["SalesforceRestClient", "SalesforceReportClient"]
except ImportError:  # requests 未導入
    pass
