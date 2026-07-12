"""
salesforce_std — Salesforce API クライアント（標準ライブラリのみ）

外部ライブラリを一切使わないため、追加インストールなしで動く。
requests が導入できる環境では salesforce_requests（同じ API）も使える。

| クラス | 依存 | 用途 |
|---|---|---|
| SalesforceApiClient | なし（標準ライブラリのみ） | CRUD・SOQL・レポート・Bulk 2.0 |
"""

from .api import SalesforceApiClient

__all__ = ["SalesforceApiClient"]
