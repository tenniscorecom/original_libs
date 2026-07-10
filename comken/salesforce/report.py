import time

import requests


class SalesforceReportClient:
    """Salesforce レポートを実行してデータを取得するクライアント。

    - 2000行以下: run() で同期取得
    - 2000行超え: run_async() で非同期取得
    """

    _API_VERSION = "v59.0"
    _ASYNC_POLL_INTERVAL = 3 # 非同期結果ポーリング間隔（秒）
    _ASYNC_TIMEOUT = 120 # 非同期タイムアウト（秒）

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
                       例: [{"column": "CREATED_DATE", "operator": "greaterThan", "value": "2026-01-01"}]

        Returns:
            [{"列名": "値", ...}, ...]
        """
        if filters:
            resp = requests.post(
                f"{self._base}/{report_id}",
                headers=self._headers,
                json={"reportMetadata": {"reportFilters": filters}},
            )
        else:
            resp = requests.get(f"{self._base}/{report_id}", headers=self._headers)

        resp.raise_for_status()
        return self._parse(resp.json())

    def run_async(self, report_id: str, filters: list[dict] | None = None) -> list[dict]:
        """レポートを非同期実行して全行データを返す（2000行超え対応）。

        Args:
            report_id: SalesforceのレポートID
            filters:   絞り込み条件（省略可）

        Returns:
            [{"列名": "値", ...}, ...]
        """
        body = {}
        if filters:
            body = {"reportMetadata": {"reportFilters": filters}}

        resp = requests.post(
            f"{self._base}/{report_id}/instances",
            headers=self._headers,
            json=body,
        )
        resp.raise_for_status()
        instance_id = resp.json()["id"]

        # 完了まで待機
        elapsed = 0
        while elapsed < self._ASYNC_TIMEOUT:
            result = requests.get(
                f"{self._base}/{report_id}/instances/{instance_id}",
                headers=self._headers,
            )
            result.raise_for_status()
            data = result.json()
            if data["status"] == "Success":
                return self._parse(data)
            if data["status"] == "Error":
                raise RuntimeError(f"レポート実行エラー: {data.get('errorCode')}")
            time.sleep(self._ASYNC_POLL_INTERVAL)
            elapsed += self._ASYNC_POLL_INTERVAL

        raise TimeoutError(f"レポートの取得がタイムアウトしました（{self._ASYNC_TIMEOUT}秒）")

    def _parse(self, data: dict) -> list[dict]:
        """API レスポンスを [{表示名: 値, ...}] の形式に変換する。"""
        columns = data["reportMetadata"]["detailColumns"]
        col_info = data.get("reportExtendedMetadata", {}).get("detailColumnInfo", {})

        # 表示名が取れればそちらを使い、なければ内部名をそのまま使う
        labels = [col_info.get(col, {}).get("label", col) for col in columns]

        rows = data.get("factMap", {}).get("T!T", {}).get("rows", [])
        return [
            {label: row["dataCells"][i]["label"] for i, label in enumerate(labels)}
            for row in rows
        ]
