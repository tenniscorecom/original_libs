"""
salesforce/report.py — Salesforce レポート取得クライアント

requests でレポート API を叩く。通常は salesforce/api.py の SalesforceApiClient を
優先し、レポートだけを軽く扱いたい場合にこのクライアントを使う。
"""

import logging
import time

import requests

from ..exceptions import SalesforceError

logger = logging.getLogger(__name__)


class SalesforceReportClient:
    """Salesforce レポートを実行してデータを取得するクライアント。

    - 2000行以下: run() で同期取得
    - 2000行超え: run_async() で非同期取得

    明細（TABULAR）形式のレポートのみ対応する。集計（サマリ / マトリックス）
    形式は run() / run_async() が SalesforceError を送出する。
    """

    _API_VERSION = "v60.0"
    _ASYNC_POLL_INTERVAL = 3  # 非同期結果ポーリング間隔（秒）
    _ASYNC_TIMEOUT = 120  # 非同期タイムアウト（秒）
    _TIMEOUT_SECONDS = 60  # HTTP リクエストのタイムアウト

    def __init__(self, instance_url: str, access_token: str) -> None:
        self._base = f"{instance_url}/services/data/{self._API_VERSION}/analytics/reports"
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def run(self, report_id: str, filters: list[dict] | None = None) -> list[dict]:
        """レポートを同期実行して行データを返す（上限 2000行）。

        Args:
            report_id: SalesforceのレポートID（15桁 or 18桁）
            filters:   絞り込み条件（省略可）
                       例: [{"column": "CREATED_DATE",
                            "operator": "greaterThan", "value": "2026-01-01"}]

        Returns:
            [{"列名": "値", ...}, ...]

        Raises:
            SalesforceError: API がエラーを返した / 接続失敗 / 集計形式レポートの場合。
        """
        if filters:
            data = self._request(
                "POST",
                f"{self._base}/{report_id}",
                json={"reportMetadata": {"reportFilters": filters}},
            )
        else:
            data = self._request("GET", f"{self._base}/{report_id}")
        return self._parse(data)

    def run_async(self, report_id: str, filters: list[dict] | None = None) -> list[dict]:
        """レポートを非同期実行して全行データを返す（2000行超え対応）。

        Args:
            report_id: SalesforceのレポートID
            filters:   絞り込み条件（省略可）

        Returns:
            [{"列名": "値", ...}, ...]

        Raises:
            SalesforceError: レポートの実行がエラーになった / 接続失敗 / 集計形式の場合。
            TimeoutError: タイムアウトまでに完了しなかった場合。
        """
        body = {"reportMetadata": {"reportFilters": filters}} if filters else {}
        instance = self._request("POST", f"{self._base}/{report_id}/instances", json=body)
        instance_id = instance["id"]

        deadline = time.monotonic() + self._ASYNC_TIMEOUT
        while time.monotonic() < deadline:
            data = self._request("GET", f"{self._base}/{report_id}/instances/{instance_id}")
            if data["status"] == "Success":
                return self._parse(data)
            if data["status"] == "Error":
                raise SalesforceError(f"レポート実行エラー: {data.get('errorCode')}")
            time.sleep(self._ASYNC_POLL_INTERVAL)

        raise TimeoutError(f"レポートの取得がタイムアウトしました（{self._ASYNC_TIMEOUT}秒）")

    def _request(self, method: str, url: str, json: dict | None = None) -> dict:
        """レポート API を呼び、JSON を返す。エラーは SalesforceError に変換する。"""
        try:
            resp = requests.request(
                method, url, headers=self._headers, json=json, timeout=self._TIMEOUT_SECONDS
            )
        except requests.exceptions.RequestException as e:
            raise SalesforceError(
                f"Salesforce に接続できませんでした: {method} {url}（詳細: {e}）"
            ) from e
        if resp.status_code >= 400:
            raise SalesforceError(
                f"Salesforce レポート API エラー（HTTP {resp.status_code}）: {resp.text}"
            )
        return resp.json()

    @staticmethod
    def _parse(data: dict) -> list[dict]:
        """API レスポンスを [{表示名: 値, ...}] の形式に変換する。

        Raises:
            SalesforceError: 集計（サマリ / マトリックス）形式のレポートの場合。
        """
        metadata = data.get("reportMetadata", {})
        report_format = metadata.get("reportFormat")
        # 集計レポートは factMap が "T!T" ではなくグループ別キーになり、
        # そのまま読むと無言で空を返すため明示的に弾く
        if report_format and report_format != "TABULAR":
            raise SalesforceError(
                f"このレポートは {report_format} 形式です。明細（TABULAR）形式のみ対応しています。"
            )

        # allData=False は上限で切り捨てられた印。全件と誤認させないため警告する
        if data.get("allData") is False:
            logger.warning(
                "レポートの行が上限で切り捨てられました（全件ではありません）。"
                "2000 行を超えるレポートは run_async を使ってください。"
            )

        columns = metadata.get("detailColumns", [])
        col_info = data.get("reportExtendedMetadata", {}).get("detailColumnInfo", {})
        labels = [col_info.get(col, {}).get("label", col) for col in columns]

        rows = data.get("factMap", {}).get("T!T", {}).get("rows", [])
        return [
            {label: row["dataCells"][i]["label"] for i, label in enumerate(labels)} for row in rows
        ]
