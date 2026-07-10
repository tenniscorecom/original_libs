"""
credentials/__main__.py — 認証情報の管理ツール（対話式）

非エンジニアでも使えるよう、起動してメニューを選ぶだけで
認証情報の登録・上書き・削除ができる。
登録した内容は Windows ログオンユーザーに紐付けて暗号化されるため、
他の人・他の PC からは読み取れない。

起動方法:
    python -m comken.credentials
"""

import getpass

from ..exceptions import CredentialNotFoundError
from .store import (
    CREDENTIALS_PATH,
    SERVICE_NAME_PATTERN,
    Credential,
    delete_credential,
    list_services,
    save_credential,
)


def main() -> None:
    print("=== comken 認証情報の管理 ===")
    while True:
        print()
        _show_services()
        print()
        print("1: 登録（新規追加・上書き）")
        print("2: 削除")
        print("q: 終了")
        choice = input("選択: ").strip().lower()
        print()

        if choice == "1":
            _register()
        elif choice == "2":
            _delete()
        elif choice == "q":
            return
        else:
            print("1, 2, q のいずれかを入力してください。")


def _show_services() -> None:
    registered = list_services()
    if registered:
        print(f"登録済みのサービス: {', '.join(registered)}")
    else:
        print("登録済みのサービスはまだありません。")


def _register() -> None:
    service = input("サービス名（例: salesforce）: ").strip()
    if not service:
        print("サービス名が入力されなかったため中止しました。")
        return
    if not SERVICE_NAME_PATTERN.fullmatch(service):
        print("サービス名に使えるのは半角英数字とアンダースコアだけです（例: salesforce, oju_sys）。")
        return
    if service in list_services():
        print(f"{service} は登録済みのため、上書きになります。")

    username = input("ユーザー名: ").strip()
    password = getpass.getpass("パスワード（入力しても画面には表示されません）: ")
    token = input("トークン等（不要なら Enter）: ").strip()

    save_credential(service, Credential(username, password, token))
    print(f"保存しました: {CREDENTIALS_PATH}")


def _delete() -> None:
    service = input("削除するサービス名: ").strip()
    if not service:
        print("サービス名が入力されなかったため中止しました。")
        return

    confirm = input(f"{service} を削除します。よろしいですか？（y で実行）: ").strip().lower()
    if confirm != "y":
        print("中止しました。")
        return

    try:
        delete_credential(service)
        print(f"削除しました: {service}")
    except CredentialNotFoundError:
        print(f"サービス名が見つかりません: {service}")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        # Ctrl+C 等で中断されたときにトレースバックを出さず静かに終わる
        print("\n中断しました。")
