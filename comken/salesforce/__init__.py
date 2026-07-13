"""
salesforce — 旧 import パスの互換シム

Salesforce クライアントは salesforce_requests に移動した。
このモジュール（comken.salesforce）は旧コードを壊さないための入り口で、
新しいコードでは使わないこと:

    from comken.salesforce_requests import SalesforceApiClient
"""

from ..deprecation import warn_renamed
from ..salesforce_requests import SalesforceApiClient as _SalesforceApiClient

__all__ = ["SalesforceApiClient"]


def __getattr__(name):
    if name == "SalesforceApiClient":
        warn_renamed("comken.salesforce", "comken.salesforce_requests")
        return _SalesforceApiClient
    raise AttributeError(name)
