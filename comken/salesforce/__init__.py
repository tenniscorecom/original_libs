"""
salesforce — 旧 import パスの互換シム

Salesforce クライアントは salesforce_std（標準ライブラリのみ）と
salesforce_requests（requests 版）の2フォルダに分かれた。
どちらも同じクラス名・同じメソッドなので、import 行の変更だけで切り替えられる:

    from comken.salesforce_std import SalesforceApiClient       # 標準ライブラリ版
    from comken.salesforce_requests import SalesforceApiClient  # requests 版

このモジュール（comken.salesforce）は旧コードを壊さないための入り口で、
salesforce_std → salesforce_requests の順に探して SalesforceApiClient を返す。
新しいコードでは使わないこと。
"""

from ..deprecation import warn_renamed

try:
    from ..salesforce_std import SalesforceApiClient as _SalesforceApiClient
    _NEW_NAME = "comken.salesforce_std"
except ImportError:  # salesforce_std フォルダが削除されている環境
    from ..salesforce_requests import SalesforceApiClient as _SalesforceApiClient
    _NEW_NAME = "comken.salesforce_requests"

__all__ = ["SalesforceApiClient"]


def __getattr__(name):
    if name == "SalesforceApiClient":
        warn_renamed("comken.salesforce", _NEW_NAME)
        return _SalesforceApiClient
    raise AttributeError(name)
