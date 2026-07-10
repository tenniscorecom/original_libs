"""
credentials/store.py — 認証情報の暗号化保存（Windows DPAPI）

パスワード・トークン・ユーザー名など、config.ini に書けない機密情報・個人情報を
Windows ログオンユーザーに紐付けて暗号化し、ユーザープロファイル内に保存する。

仕組み:
    - 暗号化には Windows 標準の DPAPI を使う。暗号鍵の管理は不要で、
      Windows がログオン中のアカウントに紐付けて暗号化・復号してくれる
    - 保存先は %USERPROFILE%\\.comken\\credentials.dat（ユーザーごとに別ファイル）
    - 同じ Windows アカウントでないと復号できないため、ファイルを
      他人にコピーされても中身は読まれない

登録は対話式ツールで行う（非エンジニア向け）:
    python -m comken.credentials

使い方（コード側）:
    from comken.credentials import load_credential

    cred = load_credential("salesforce")
    cred.username   # → "user@example.com"
    cred.password   # → "xxxx"
    cred.token      # → セキュリティトークン（未登録なら空文字）
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import win32crypt

from ..exceptions import CredentialNotFoundError, InvalidServiceNameError

CREDENTIALS_PATH = Path.home() / ".comken" / "credentials.dat"

# サービス名に使える文字（半角英数字とアンダースコアのみ）
# 漢字・スペース・記号はコードや config.ini に書きにくいため弾く
SERVICE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")

# 復号失敗時に DPAPI が返す説明文字列（デバッグ用。動作には影響しない）
_FILE_DESCRIPTION = "comken credentials"


@dataclass
class Credential:
    """1サービス分の認証情報。token は不要なら空文字のまま。"""

    username: str
    password: str
    token: str = ""


def save_credential(service: str, credential: Credential, path: Path | None = None) -> None:
    """認証情報を暗号化して保存する。同じサービス名は上書きされる。

    Args:
        service: サービス名（例: "salesforce"）。取得時のキーになる。
            半角英数字とアンダースコアのみ使用できる。
        credential: 保存する認証情報。
        path: 保存先ファイル。省略時は CREDENTIALS_PATH（通常は省略する）。

    Raises:
        InvalidServiceNameError: サービス名に使えない文字が含まれている場合。
    """
    if not SERVICE_NAME_PATTERN.fullmatch(service):
        raise InvalidServiceNameError(
            f"サービス名に使えるのは半角英数字とアンダースコアだけです: {service}\n"
            f"例: salesforce, oju_sys, salesforce_test"
        )
    path = path or CREDENTIALS_PATH
    data = _load_all(path)
    data[service] = asdict(credential)
    _save_all(data, path)


def load_credential(service: str, path: Path | None = None) -> Credential:
    """保存済みの認証情報を復号して返す。

    Args:
        service: 登録時に指定したサービス名。

    Raises:
        CredentialNotFoundError: サービス名が未登録の場合。
    """
    path = path or CREDENTIALS_PATH
    data = _load_all(path)
    if service not in data:
        raise CredentialNotFoundError(
            f"認証情報が登録されていません: {service}\n"
            f"python -m comken.credentials を実行して登録してください。"
        )
    return Credential(**data[service])


def delete_credential(service: str, path: Path | None = None) -> None:
    """登録済みの認証情報を削除する。

    Raises:
        CredentialNotFoundError: サービス名が未登録の場合。
    """
    path = path or CREDENTIALS_PATH
    data = _load_all(path)
    if service not in data:
        raise CredentialNotFoundError(f"認証情報が登録されていません: {service}")
    del data[service]
    _save_all(data, path)


def list_services(path: Path | None = None) -> list[str]:
    """登録済みのサービス名一覧を返す（認証情報そのものは返さない）。"""
    path = path or CREDENTIALS_PATH
    return sorted(_load_all(path))


def _load_all(path: Path) -> dict:
    """暗号化ファイルを復号して全サービスの辞書を返す。未作成なら空辞書。"""
    if not path.exists():
        return {}
    encrypted = path.read_bytes()
    _, decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
    return json.loads(decrypted.decode("utf-8"))


def _save_all(data: dict, path: Path) -> None:
    """全サービスの辞書を暗号化してファイルに書き込む。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
    encrypted = win32crypt.CryptProtectData(raw, _FILE_DESCRIPTION, None, None, None, 0)
    path.write_bytes(encrypted)
