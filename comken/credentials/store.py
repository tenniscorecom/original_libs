"""
credentials/store.py — 認証情報の暗号化保存（Windows DPAPI）

パスワード・トークン・ユーザー名など、config.ini に書けない機密情報・個人情報を
Windows ログオンユーザーに紐付けて暗号化し、ユーザープロファイル内に保存する。

キー名1つに値1つを登録するシンプルな形式。
「ユーザー名とパスワードが必ずセット」という決め打ちをしないため、
パスワードだけ・トークンだけのシステムにも対応できる。

仕組み:
    - 暗号化には Windows 標準の DPAPI を使う。暗号鍵の管理は不要で、
      Windows がログオン中のアカウントに紐付けて暗号化・復号してくれる
    - 保存先は %USERPROFILE%\\.comken\\credentials.dat（ユーザーごとに別ファイル）
    - 同じ「ユーザー × PC」でないと復号できないため、ファイルを
      他人にコピーされても中身は読まれない

登録は対話式ツールで行う（非エンジニア向け）:
    python -m comken.credentials

使い方（コード側）:
    from comken.credentials import Credentials

    sf = Credentials("salesforce")
    sf.username   # → salesforce_username の値
    sf.password   # → salesforce_password の値

    # 1件だけ取り出す場合
    from comken.credentials import load_credential
    password = load_credential("oju_sys_password")
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import win32crypt

from ..exceptions import CredentialNotFoundError, InvalidCredentialNameError
from ..utils.file import cleanup_stale_tmp as _cleanup_stale_tmp

CREDENTIALS_PATH = Path.home() / ".comken" / "credentials.dat"

# キー名に使える文字（半角英数字とアンダースコアのみ）
# 漢字・スペース・記号はコードや config.ini に書きにくいため弾く
CREDENTIAL_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")

# 復号失敗時に DPAPI が返す説明文字列（デバッグ用。動作には影響しない）
_FILE_DESCRIPTION = "comken credentials"


class Credentials:
    """プレフィックス配下の認証情報に属性アクセスでまとめてアクセスする。

    キー名「システム名_項目名」のシステム名部分だけを指定し、項目名は属性で取り出す。
    プレフィックスを config.ini から渡せば、本番用・テスト用アカウントの切り替えが
    config.ini の1行だけで済む（コード側にキー名の直書きが残らない）。

    使い方:
        sf = Credentials("salesforce")
        sf.username   # → load_credential("salesforce_username") と同じ
        sf.password   # → load_credential("salesforce_password") と同じ

        # config.ini で本番・テストを切り替える場合
        # [CREDENTIALS]
        # SALESFORCE = salesforce      ← salesforce_test にすると全項目が切り替わる
        sf = Credentials(config.CREDENTIALS.SALESFORCE)

    Raises:
        InvalidCredentialNameError: プレフィックスに使えない文字が含まれている場合。
        CredentialNotFoundError: 属性に対応するキーが未登録の場合。
    """

    def __init__(self, prefix: str, path: Path | None = None) -> None:
        """
        Args:
            prefix: キー名のシステム名部分（例: "salesforce", "salesforce_test"）。
            path: 保存先ファイル。省略時は CREDENTIALS_PATH（通常は省略する）。
        """
        if not CREDENTIAL_NAME_PATTERN.fullmatch(prefix):
            raise InvalidCredentialNameError(
                InvalidCredentialNameError.MSG_PREFIX.format(name=prefix)
            )
        self._prefix = prefix
        self._path = path

    def __getattr__(self, item: str) -> str:
        # _ 始まりは Python 内部の属性探索（copy 等）なので通常の AttributeError にする
        if item.startswith("_"):
            raise AttributeError(item)
        return load_credential(f"{self._prefix}_{item}", self._path)


def save_credential(name: str, value: str, path: Path | None = None) -> None:
    """認証情報を暗号化して保存する。同じキー名は上書きされる。

    Args:
        name: キー名（例: "salesforce_password"）。取得時のキーになる。
            半角英数字とアンダースコアのみ使用できる。
        value: 保存する値（パスワード・トークン・ユーザー名など）。
        path: 保存先ファイル。省略時は CREDENTIALS_PATH（通常は省略する）。

    Raises:
        InvalidCredentialNameError: キー名に使えない文字が含まれている場合。
    """
    if not CREDENTIAL_NAME_PATTERN.fullmatch(name):
        raise InvalidCredentialNameError(InvalidCredentialNameError.MSG_KEY.format(name=name))
    path = path or CREDENTIALS_PATH
    data = _load_all(path)
    data[name] = value
    _save_all(data, path)


def load_credential(name: str, path: Path | None = None) -> str:
    """保存済みの認証情報を復号して返す。

    Args:
        name: 登録時に指定したキー名。

    Raises:
        CredentialNotFoundError: キー名が未登録の場合。
    """
    path = path or CREDENTIALS_PATH
    data = _load_all(path)
    if name not in data:
        raise CredentialNotFoundError(CredentialNotFoundError.MSG.format(name=name))
    return data[name]


def delete_credential(name: str, path: Path | None = None) -> None:
    """登録済みの認証情報を削除する。

    Raises:
        CredentialNotFoundError: キー名が未登録の場合。
    """
    path = path or CREDENTIALS_PATH
    data = _load_all(path)
    if name not in data:
        raise CredentialNotFoundError(CredentialNotFoundError.MSG.format(name=name))
    del data[name]
    _save_all(data, path)


def list_names(path: Path | None = None) -> list[str]:
    """登録済みのキー名一覧を返す（値そのものは返さない）。"""
    path = path or CREDENTIALS_PATH
    return sorted(_load_all(path))


def _load_all(path: Path) -> dict[str, str]:
    """暗号化ファイルを復号して全キーの辞書を返す。未作成なら空辞書。"""
    if not path.exists():
        return {}
    encrypted = path.read_bytes()
    _, decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
    return json.loads(decrypted.decode("utf-8"))


def _save_all(data: dict[str, str], path: Path) -> None:
    """全キーの辞書を暗号化してファイルに書き込む。

    一時ファイル経由でアトミックに置き換える（同時書き込みや書き込み中の
    クラッシュで暗号化ファイルが半端に壊れ、全キーが読めなくなるのを防ぐ）。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    _cleanup_stale_tmp(path)  # 前回クラッシュ時の .tmp 残骸を掃除
    raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
    encrypted = win32crypt.CryptProtectData(raw, _FILE_DESCRIPTION, None, None, None, 0)
    tmp_path = path.with_suffix(f".dat.{os.getpid()}.tmp")
    tmp_path.write_bytes(encrypted)
    os.replace(tmp_path, path)
