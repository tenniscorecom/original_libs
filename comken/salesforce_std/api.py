"""
salesforce_std/api.py — Salesforce API クライアント（標準ライブラリのみ）

外部ライブラリ（simple-salesforce / requests）をインストールできない環境向けに、
urllib・json・xml など Python 標準ライブラリだけで Salesforce の API を直接呼ぶ。
requests が導入できる環境では salesforce_requests 版（同じ API・同じクラス名）も使える。

対応している操作:
    - ログイン（SOAP ログイン。接続アプリケーション不要）
    - SOQL クエリ（全件取得・ページネーション自動）
    - レコードの取得・作成・更新・Upsert・削除
    - レポートの実行（同期 / 非同期・絞り込み対応）
    - Bulk API 2.0（大量レコードの一括 insert / update / upsert / delete / query）

使い方:
    from comken.credentials import Credentials
    from comken.salesforce_std import SalesforceApiClient

    cred = Credentials("salesforce")
    sf = SalesforceApiClient(
        username=cred.username,
        password=cred.password,
        security_token=cred.token,
        # domain="test",  # Sandbox の場合
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
import json
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from ..exceptions import SalesforceError
from ..runtime import dry_run_log, is_dry_run

# SOAP ログインのレスポンス XML の名前空間
_SOAP_NS = "{urn:partner.soap.sforce.com}"


class SalesforceApiClient:
    """Salesforce API クライアント（標準ライブラリのみで動く）。

    接続アプリケーション（client_id / client_secret）は不要。
    ユーザー名・パスワード・セキュリティトークンだけでログインする。

    使い方:
        sf = SalesforceApiClient(
            username="user@example.com",
            password="password",
            security_token="トークン",
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
        username: str,
        password: str,
        security_token: str,
        domain: str = "login",
    ) -> None:
        """
        Args:
            username: Salesforce のログインユーザー名（メールアドレス形式）。
            password: パスワード。
            security_token: セキュリティトークン（プロフィール設定から取得）。
            domain: 接続先。本番環境は "login"、Sandbox は "test"。

        Raises:
            SalesforceError: ログインに失敗した場合。
        """
        self._session_id, self._instance_url = self._login(
            username, password, security_token, domain
        )

    # ------------------------------------------------------------------ login
    def _login(
        self, username: str, password: str, security_token: str, domain: str
    ) -> tuple[str, str]:
        """SOAP ログインでセッション ID とインスタンス URL を取得する。"""
        url = f"https://{domain}.salesforce.com/services/Soap/u/{self.API_VERSION}"
        body = f"""<?xml version="1.0" encoding="utf-8" ?>
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"
              xmlns:urn="urn:partner.soap.sforce.com">
  <env:Body>
    <urn:login>
      <urn:username>{escape(username)}</urn:username>
      <urn:password>{escape(password + security_token)}</urn:password>
    </urn:login>
  </env:Body>
</env:Envelope>"""
        request = urllib.request.Request(
            url,
            data=body.encode("utf-8"),
            method="POST",
            headers={"Content-Type": "text/xml; charset=UTF-8", "SOAPAction": "login"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.TIMEOUT_SECONDS) as resp:
                return _parse_login_response(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # ログイン失敗時も SOAP は 500 + fault XML を返すのでパースを試みる
            return _parse_login_response(e.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise SalesforceError(
                f"Salesforce に接続できませんでした: {url}\n"
                f"ネットワーク接続を確認してください。（詳細: {e.reason}）"
            ) from e

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
        data = raw_body
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        request = urllib.request.Request(
            f"{self._instance_url}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self._session_id}",
                "Content-Type": content_type,
                "Accept": "application/json, text/csv",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.TIMEOUT_SECONDS) as resp:
                text = resp.read().decode("utf-8")
                headers = dict(resp.headers)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise SalesforceError(
                f"Salesforce API エラー（HTTP {e.code}）: {method} {path}\n{detail}"
            ) from e
        except urllib.error.URLError as e:
            raise SalesforceError(
                f"Salesforce に接続できませんでした: {method} {path}（詳細: {e.reason}）"
            ) from e

        if not text:
            return None, headers
        if headers.get("Content-Type", "").startswith("application/json"):
            return json.loads(text), headers
        return text, headers

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
        while True:
            for record in result["records"]:
                record.pop("attributes", None)  # メタ情報は業務データに不要なので除く
                records.append(record)
            if result.get("done"):
                return records
            result, _ = self._request("GET", result["nextRecordsUrl"])

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
        """レポート API のレスポンスを [{表示名: 値, ...}] に変換する。"""
        columns = data["reportMetadata"]["detailColumns"]
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

def _parse_login_response(xml_text: str) -> tuple[str, str]:
    """SOAP ログインのレスポンスから (セッションID, インスタンスURL) を取り出す。

    Raises:
        SalesforceError: ログイン失敗（faultstring がある）または形式が不正な場合。
    """
    root = ET.fromstring(xml_text)

    fault = root.find(".//faultstring")
    if fault is not None:
        raise SalesforceError(
            f"Salesforce へのログインに失敗しました: {fault.text}\n"
            f"ユーザー名・パスワード・セキュリティトークンを確認してください。\n"
            f"（パスワードを変更するとトークンも新しくなります。"
            f"python -m comken.credentials で登録し直してください）"
        )

    session_id = root.find(f".//{_SOAP_NS}sessionId")
    server_url = root.find(f".//{_SOAP_NS}serverUrl")
    if session_id is None or server_url is None:
        raise SalesforceError(f"ログインレスポンスを解釈できませんでした: {xml_text[:200]}")

    # serverUrl は https://xxx.my.salesforce.com/services/Soap/u/60.0/00D... の形式。
    # インスタンス URL 部分（/services より前）だけを使う
    instance_url = server_url.text.split("/services")[0]
    return session_id.text, instance_url


def _dicts_to_csv(records: list[dict]) -> str:
    """辞書のリストを Bulk API 用の CSV 文字列に変換する。"""
    fieldnames = list(records[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return buf.getvalue()


def _csv_to_dicts(text: str) -> list[dict]:
    """Bulk API が返す CSV 文字列を辞書のリストに変換する。"""
    return list(csv.DictReader(io.StringIO(text)))
