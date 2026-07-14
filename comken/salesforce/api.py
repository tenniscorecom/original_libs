"""
salesforce/api.py — Salesforce API クライアント（requests 版）

認証は OAuth 2.0 のクライアントクレデンシャルフローを使う。
接続アプリケーション（Connected App）の client_id / client_secret だけで、
毎回アクセストークンを取り直す。ユーザー名・パスワード・セキュリティトークンは使わない
（無人 RPA 向け。リフレッシュトークンの保管・失効も発生しない）。

事前に Salesforce 側で必要な設定（管理者作業。詳細は docs/Salesforce認証パターン.md）:
    1. インテグレーション用ユーザーを作る（API 権限のみ）
    2. 接続アプリを作り、OAuth 有効化 + スコープ「api」+
       「クライアントクレデンシャルフローを有効化」にチェック
       （新規は External Client App を推奨。旧 Connected App でも可）
    3. アプリのポリシーで「実行ユーザー（Run As）」に 1 のユーザーを指定
    4. Consumer Key（= client_id）と Consumer Secret（= client_secret）を控える

通信は requests を使う（Session による接続再利用で連続リクエストが速い）。

対応している操作:
    - 認証（OAuth 2.0 クライアントクレデンシャル）
    - SOQL クエリ（全件取得・ページネーション自動）
    - レコードの取得・作成・更新・Upsert・削除
    - レポートの実行（同期 / 非同期・絞り込み対応）
    - Bulk API 2.0（大量レコードの一括 insert / update / upsert / delete / query）

使い方:
    from comken.credentials import Credentials
    from comken.salesforce import SalesforceApiClient

    cred = Credentials("salesforce")
    sf = SalesforceApiClient(
        client_id=cred.client_id,
        client_secret=cred.client_secret,
        domain_url="https://your-domain.my.salesforce.com",  # 組織の My Domain
    )

    records = sf.query("SELECT Id, Name FROM Account")
    new_id = sf.insert("Account", {"Name": "新規取引先"})
    sf.update("Account", record_id=new_id, data={"Name": "更新後"})
    sf.delete("Account", record_id=new_id)

    rows = sf.run_report("00O000000000001")

    result = sf.bulk_insert("Account", [{"Name": f"取引先{i}"} for i in range(10000)])
"""

import csv
import io
import logging
import time
import urllib.parse

import requests

from ..exceptions import SalesforceError
from ..runtime import dry_run_log, is_dry_run

logger = logging.getLogger(__name__)


class SalesforceApiClient:
    """Salesforce API クライアント（requests 版）。

    OAuth 2.0 クライアントクレデンシャルフローで認証する。
    接続アプリケーションの client_id / client_secret だけを使い、
    ユーザー名・パスワード・セキュリティトークンは使わない。

    使い方:
        sf = SalesforceApiClient(
            client_id="接続アプリの Consumer Key",
            client_secret="接続アプリの Consumer Secret",
            domain_url="https://your-domain.my.salesforce.com",
        )
        records = sf.query("SELECT Id, Name FROM Account")
    """

    API_VERSION = "60.0"
    TIMEOUT_SECONDS = 60  # HTTP リクエストのタイムアウト
    BULK_POLL_INTERVAL = 3  # Bulk ジョブのポーリング間隔（秒）
    BULK_TIMEOUT = 600  # Bulk ジョブの完了待ちタイムアウト（秒）
    REPORT_POLL_INTERVAL = 3  # 非同期レポートのポーリング間隔（秒）
    REPORT_TIMEOUT = 120  # 非同期レポートのタイムアウト（秒）

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        domain_url: str,
    ) -> None:
        """
        Args:
            client_id: 接続アプリケーションの Consumer Key。
            client_secret: 接続アプリケーションの Consumer Secret。
            domain_url: 組織の My Domain の URL（例: "https://foo.my.salesforce.com"）。
                        Sandbox は "https://foo--sandbox.sandbox.my.salesforce.com"。
                        ※ クライアントクレデンシャルフローは My Domain が必須で、
                          login.salesforce.com では動かない。

        Raises:
            SalesforceError: 認証に失敗した場合。
        """
        self._session = requests.Session()
        self._access_token, self._instance_url = self._login(client_id, client_secret, domain_url)
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._access_token}",
                "Accept": "application/json, text/csv",
            }
        )

    def __enter__(self) -> "SalesforceApiClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def close(self) -> None:
        """HTTP セッションを閉じる。with 文を使う場合は自動で呼ばれる。"""
        self._session.close()

    # ------------------------------------------------------------------ login
    def _login(self, client_id: str, client_secret: str, domain_url: str) -> tuple[str, str]:
        """クライアントクレデンシャルフローでアクセストークンとインスタンス URL を取得する。"""
        url = f"{domain_url.rstrip('/')}/services/oauth2/token"
        try:
            resp = self._session.post(
                url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                timeout=self.TIMEOUT_SECONDS,
            )
        except requests.exceptions.RequestException as e:
            raise SalesforceError(
                f"Salesforce に接続できませんでした: {url}\n"
                f"ネットワーク接続と My Domain の URL を確認してください。（詳細: {e}）"
            ) from e
        if resp.status_code >= 400:
            raise SalesforceError(
                f"Salesforce の認証に失敗しました（HTTP {resp.status_code}）: {resp.text}\n"
                "接続アプリの client_id / client_secret、"
                "クライアントクレデンシャルフローの有効化と実行ユーザー（Run As）の指定、"
                "My Domain の URL を確認してください。"
            )
        body = resp.json()
        return body["access_token"], body["instance_url"]

    # ---------------------------------------------------------------- request
    def _request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        raw_body: bytes | None = None,
        content_type: str = "application/json",
    ) -> tuple[dict | list | str | None, dict]:
        """REST API を呼び、(レスポンスボディ, レスポンスヘッダー) を返す。

        Args:
            method: HTTP メソッド（GET / POST / PATCH / PUT / DELETE）。
            path: /services/data/... から始まるパス。
            body: JSON で送る辞書（省略可）。
            raw_body: CSV 等をそのまま送る場合のバイト列（body と排他）。
            content_type: raw_body 使用時の Content-Type。

        Raises:
            SalesforceError: API がエラーを返した場合（メッセージに詳細を含む）。
        """
        try:
            resp = self._session.request(
                method,
                f"{self._instance_url}{path}",
                json=body,
                data=raw_body,
                headers={"Content-Type": content_type},
                timeout=self.TIMEOUT_SECONDS,
            )
        except requests.exceptions.RequestException as e:
            raise SalesforceError(
                f"Salesforce に接続できませんでした: {method} {path}（詳細: {e}）"
            ) from e

        if resp.status_code >= 400:
            raise SalesforceError(
                f"Salesforce API エラー（HTTP {resp.status_code}）: {method} {path}\n{resp.text}"
            )

        headers = dict(resp.headers)
        if not resp.text:
            return None, headers
        if headers.get("Content-Type", "").startswith("application/json"):
            return resp.json(), headers
        return resp.text, headers

    def _data_path(self, path: str) -> str:
        return f"/services/data/v{self.API_VERSION}{path}"

    # ------------------------------------------------------------------ query
    def query(self, soql: str) -> list[dict]:
        """SOQL クエリを実行してレコードを返す（全件取得・ページネーション自動）。

        Args:
            soql: 実行する SOQL クエリ文字列。

        Returns:
            レコードの辞書のリスト。
        """
        records: list[dict] = []
        result, _ = self._request("GET", self._data_path(f"/query?q={urllib.parse.quote(soql)}"))
        # 想定外のレスポンス形（dict 以外）でも素の KeyError を出さず安全に抜ける
        while isinstance(result, dict):
            for record in result.get("records", []):
                record.pop("attributes", None)  # メタ情報は業務データに不要なので除く
                records.append(record)
            next_url = result.get("nextRecordsUrl")
            if result.get("done", True) or not next_url:
                break
            result, _ = self._request("GET", next_url)
        return records

    # ------------------------------------------------------------------- CRUD
    def get(self, object_name: str, record_id: str) -> dict:
        """レコードを1件取得する。

        Args:
            object_name: オブジェクト API 名（例: "Account", "CustomObj__c"）。
            record_id: レコードの Id。
        """
        record, _ = self._request("GET", self._data_path(f"/sobjects/{object_name}/{record_id}"))
        record.pop("attributes", None)
        return record

    def insert(self, object_name: str, data: dict) -> str:
        """レコードを作成して Id を返す。

        Args:
            object_name: オブジェクト API 名。
            data: 作成するレコードのフィールド値の辞書。
        """
        if is_dry_run():
            dry_run_log("Salesforce %s に insert: %s", object_name, data)
            return "DRYRUN00000000000A"
        result, _ = self._request("POST", self._data_path(f"/sobjects/{object_name}/"), body=data)
        return result["id"]

    def update(self, object_name: str, record_id: str, data: dict) -> None:
        """レコードを更新する。

        Args:
            object_name: オブジェクト API 名。
            record_id: 更新するレコードの Id。
            data: 更新するフィールド値の辞書。
        """
        if is_dry_run():
            dry_run_log("Salesforce %s (%s) を update: %s", object_name, record_id, data)
            return
        self._request("PATCH", self._data_path(f"/sobjects/{object_name}/{record_id}"), body=data)

    def upsert(self, object_name: str, external_id_field: str, data: dict) -> None:
        """外部 ID を使って Upsert する（一致すれば更新、なければ作成）。

        Args:
            object_name: オブジェクト API 名。
            external_id_field: 外部 ID フィールドの API 名（例: "ExternalId__c"）。
            data: フィールド値の辞書。external_id_field の値を含むこと。
        """
        if is_dry_run():
            dry_run_log("Salesforce %s を upsert（%s）: %s", object_name, external_id_field, data)
            return
        external_id = urllib.parse.quote(str(data[external_id_field]))
        body = {k: v for k, v in data.items() if k != external_id_field}
        self._request(
            "PATCH",
            self._data_path(f"/sobjects/{object_name}/{external_id_field}/{external_id}"),
            body=body,
        )

    def delete(self, object_name: str, record_id: str) -> None:
        """レコードを削除する。

        Args:
            object_name: オブジェクト API 名。
            record_id: 削除するレコードの Id。
        """
        if is_dry_run():
            dry_run_log("Salesforce %s (%s) を delete", object_name, record_id)
            return
        self._request("DELETE", self._data_path(f"/sobjects/{object_name}/{record_id}"))

    # ----------------------------------------------------------------- report
    def run_report(self, report_id: str, filters: list[dict] | None = None) -> list[dict]:
        """レポートを同期実行して行データを返す（上限 2000 行）。

        2000 行を超えるレポートは run_report_async() を使う。

        Args:
            report_id: レポート ID（レポートを開いたときの URL 末尾。15桁 or 18桁）。
            filters: 絞り込み条件（省略可）。
                例: [{"column": "CREATED_DATE", "operator": "greaterThan", "value": "2026-01-01"}]

        Returns:
            [{"列の表示名": "値", ...}, ...] のリスト。
        """
        path = self._data_path(f"/analytics/reports/{report_id}")
        if filters:
            data, _ = self._request(
                "POST", path, body={"reportMetadata": {"reportFilters": filters}}
            )
        else:
            data, _ = self._request("GET", path)
        return self._parse_report(data)

    def run_report_async(self, report_id: str, filters: list[dict] | None = None) -> list[dict]:
        """レポートを非同期実行して全行データを返す（2000 行超え対応）。

        Args:
            report_id: レポート ID。
            filters: 絞り込み条件（省略可）。

        Raises:
            SalesforceError: レポートの実行がエラーになった場合。
            TimeoutError: REPORT_TIMEOUT 秒以内に完了しなかった場合。
        """
        base = self._data_path(f"/analytics/reports/{report_id}/instances")
        body = {"reportMetadata": {"reportFilters": filters}} if filters else {}
        result, _ = self._request("POST", base, body=body)
        instance_id = result["id"]

        deadline = time.monotonic() + self.REPORT_TIMEOUT
        while time.monotonic() < deadline:
            data, _ = self._request("GET", f"{base}/{instance_id}")
            if data["status"] == "Success":
                return self._parse_report(data)
            if data["status"] == "Error":
                raise SalesforceError(f"レポートの実行に失敗しました: {data.get('errorCode')}")
            time.sleep(self.REPORT_POLL_INTERVAL)

        raise TimeoutError(f"レポートの取得がタイムアウトしました（{self.REPORT_TIMEOUT}秒）")

    @staticmethod
    def _parse_report(data: dict) -> list[dict]:
        """レポート API のレスポンスを [{表示名: 値, ...}] に変換する。

        Raises:
            SalesforceError: 集計（サマリ / マトリックス）形式のレポートの場合。
                             この整形は明細（TABULAR）形式のみに対応している。
        """
        metadata = data.get("reportMetadata", {})
        report_format = metadata.get("reportFormat")
        # 集計レポートは factMap が "T!T" ではなくグループ別キーになり、
        # そのまま "T!T" を読むと無言で空を返してしまうため明示的に弾く
        if report_format and report_format != "TABULAR":
            raise SalesforceError(
                f"このレポートは {report_format} 形式です。"
                "run_report / run_report_async は明細（TABULAR）形式のみ対応しています。\n"
                "レポート側を明細形式に変更するか、SOQL（query）で取得してください。"
            )

        # allData=False は「上限で切り捨てられた」印。全件と誤認させないため警告する
        if data.get("allData") is False:
            logger.warning(
                "レポートの行が上限で切り捨てられました（全件ではありません）。"
                "2000 行を超えるレポートは run_report_async を使ってください。"
            )

        columns = metadata.get("detailColumns", [])
        col_info = data.get("reportExtendedMetadata", {}).get("detailColumnInfo", {})
        # 表示名が取れればそちらを使い、なければ内部名をそのまま使う
        labels = [col_info.get(col, {}).get("label", col) for col in columns]

        rows = data.get("factMap", {}).get("T!T", {}).get("rows", [])
        return [
            {label: row["dataCells"][i]["label"] for i, label in enumerate(labels)} for row in rows
        ]

    # --------------------------------------------------------------- Bulk 2.0
    # 1000 件を超える大量レコードの一括操作。少量なら通常の CRUD を使うこと。
    def bulk_insert(self, object_name: str, records: list[dict]) -> dict:
        """レコードを一括 insert する。

        Args:
            object_name: オブジェクト API 名。
            records: 挿入するレコードのリスト（"Id" は含めない）。

        Returns:
            {"success": 成功件数, "failed": 失敗行のリスト（sf__Error 列にエラー内容）}
        """
        return self._bulk_ingest(object_name, "insert", records)

    def bulk_update(self, object_name: str, records: list[dict]) -> dict:
        """レコードを一括 update する。各レコードに "Id" キーが必要。"""
        return self._bulk_ingest(object_name, "update", records)

    def bulk_upsert(self, object_name: str, records: list[dict], external_id_field: str) -> dict:
        """外部 ID で一括 upsert する。各レコードに external_id_field の値が必要。"""
        return self._bulk_ingest(
            object_name, "upsert", records, external_id_field=external_id_field
        )

    def bulk_delete(self, object_name: str, records: list[dict]) -> dict:
        """レコードを一括 delete する。各レコードは {"Id": "..."} だけでよい。"""
        return self._bulk_ingest(object_name, "delete", records)

    def bulk_query(self, soql: str) -> list[dict]:
        """SOQL クエリを Bulk API で実行する（数万件以上の大量取得向け）。

        Args:
            soql: 実行する SOQL クエリ文字列。

        Returns:
            レコードの辞書のリスト（値はすべて文字列）。
        """
        job, _ = self._request(
            "POST",
            self._data_path("/jobs/query"),
            body={"operation": "query", "query": soql},
        )
        job_id = job["id"]
        self._wait_for_bulk_job(self._data_path(f"/jobs/query/{job_id}"))

        # 結果は CSV。件数が多いと分割されるので Sforce-Locator が尽きるまで取得する
        records: list[dict] = []
        locator = ""
        while True:
            path = self._data_path(f"/jobs/query/{job_id}/results")
            if locator:
                path += f"?locator={locator}"
            text, headers = self._request("GET", path)
            if text:  # 0 件のページでは本文が空になり得るので None/空をガードする
                records.extend(_csv_to_dicts(text))
            locator = headers.get("Sforce-Locator", "")
            if not locator or locator == "null":
                return records

    def _bulk_ingest(
        self,
        object_name: str,
        operation: str,
        records: list[dict],
        external_id_field: str | None = None,
    ) -> dict:
        """Bulk API 2.0 の取り込みジョブ（insert / update / upsert / delete）を実行する。"""
        if not records:
            return {"success": 0, "failed": []}
        if is_dry_run():
            dry_run_log("Salesforce %s に bulk %s: %d 件", object_name, operation, len(records))
            return {"success": 0, "failed": []}

        job_body = {"object": object_name, "operation": operation, "contentType": "CSV"}
        if external_id_field:
            job_body["externalIdFieldName"] = external_id_field

        job, _ = self._request("POST", self._data_path("/jobs/ingest"), body=job_body)
        job_id = job["id"]
        job_path = self._data_path(f"/jobs/ingest/{job_id}")

        # CSV をアップロードして「アップロード完了」を宣言すると処理が始まる
        self._request(
            "PUT",
            f"{job_path}/batches",
            raw_body=_dicts_to_csv(records).encode("utf-8"),
            content_type="text/csv",
        )
        self._request("PATCH", job_path, body={"state": "UploadComplete"})
        result = self._wait_for_bulk_job(job_path)

        failed_text, _ = self._request("GET", f"{job_path}/failedResults/")
        failed = _csv_to_dicts(failed_text) if isinstance(failed_text, str) else []
        return {
            "success": result.get("numberRecordsProcessed", 0)
            - result.get("numberRecordsFailed", 0),
            "failed": failed,
        }

    def _wait_for_bulk_job(self, job_path: str) -> dict:
        """Bulk ジョブが完了するまでポーリングする。

        Raises:
            SalesforceError: ジョブが失敗・中断した場合。
            TimeoutError: BULK_TIMEOUT 秒以内に完了しなかった場合。
        """
        deadline = time.monotonic() + self.BULK_TIMEOUT
        while time.monotonic() < deadline:
            job, _ = self._request("GET", job_path)
            if job["state"] == "JobComplete":
                return job
            if job["state"] in ("Failed", "Aborted"):
                raise SalesforceError(
                    f"Bulk ジョブが失敗しました（state: {job['state']}）: "
                    f"{job.get('errorMessage', '')}"
                )
            time.sleep(self.BULK_POLL_INTERVAL)

        raise TimeoutError(f"Bulk ジョブがタイムアウトしました（{self.BULK_TIMEOUT}秒）")


# ── 内部ヘルパー ──────────────────────────────────────────────────────────────


def _dicts_to_csv(records: list[dict]) -> str:
    """辞書のリストを Bulk API 用の CSV 文字列に変換する。

    先頭行だけでなく全レコードのキーの和集合をヘッダーにする
    （先頭行にないキーを持つ行で ValueError にならないようにする）。
    行ごとに欠けているキーは空欄になる。
    """
    fieldnames = list(dict.fromkeys(key for record in records for key in record))
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return buf.getvalue()


def _csv_to_dicts(text: str) -> list[dict]:
    """Bulk API が返す CSV 文字列を辞書のリストに変換する。"""
    return list(csv.DictReader(io.StringIO(text)))
