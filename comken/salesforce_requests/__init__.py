"""
salesforce_requests — Salesforce API クライアント（requests / 外部ライブラリ版）

salesforce_std と同じ API の requests 版。どちらを使うかは import 行で切り替える:

    from comken.salesforce_std import SalesforceApiClient       # 標準ライブラリ版
    from comken.salesforce_requests import SalesforceApiClient  # requests 版

requests が導入できない環境では、このフォルダ（salesforce_requests）ごと削除してよい。

| クラス | 依存 | 用途 |
|---|---|---|
| SalesforceApiClient（推奨） | requests | CRUD・SOQL・レポート・Bulk 2.0 |
| SalesforceClient | simple-salesforce | CRUD・SOQL |
| SalesforceBulkClient | simple-salesforce | Bulk 一括操作 |
| SalesforceRestClient | requests | REST API 直接操作 |
| SalesforceReportClient | requests | レポート取得 |
"""

from .api import SalesforceApiClient
from .report import SalesforceReportClient
from .rest_api import SalesforceRestClient

__all__ = ["SalesforceApiClient", "SalesforceRestClient", "SalesforceReportClient"]

# simple-salesforce 版はインストールされている場合だけ使える（未導入でも import エラーにしない）
try:
    from .bulk import SalesforceBulkClient
    from .simple_sf import SalesforceClient

    __all__ += ["SalesforceClient", "SalesforceBulkClient"]
except ImportError:  # simple-salesforce 未導入
    pass
