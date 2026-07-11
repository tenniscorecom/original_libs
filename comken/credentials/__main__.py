"""
credentials/__main__.py — 認証情報の管理ツール（対話式）

非エンジニアでも使えるよう、起動してメニューを選ぶだけで
認証情報の登録・上書き・削除ができる。
登録した内容は Windows ログオンユーザーに紐付けて暗号化されるため、
他の人・他の PC からは読み取れない。

起動方法:
    python -m comken.credentials

プロジェクトのフォルダ（main.py がある場所）で起動すると、
コード内の REQUIRED_CREDENTIALS 宣言を読み取り、
「まとめて登録」メニューで未登録の分だけ順に入力できる。

    # src/credentials.py（プロジェクト側で宣言しておく）
    REQUIRED_CREDENTIALS = {
        "SALESFORCE": ["username", "password", "token"],
        "OJU_SYS": ["password"],
    }
"""

import ast
import configparser
import getpass
from pathlib import Path

from ..exceptions import CredentialNotFoundError
from .store import (
    CREDENTIAL_NAME_PATTERN,
    CREDENTIALS_PATH,
    delete_credential,
    list_names,
    save_credential,
)


def main() -> None:
    print("=== comken 認証情報の管理 ===")
    required = _read_declared_credentials()
    while True:
        print()
        _show_names()
        print()
        print("1: 登録（新規追加・上書き）")
        print("2: 削除")
        if required:
            print("3: このプロジェクトに必要な項目をまとめて登録")
        print("q: 終了")
        choice = input("選択: ").strip().lower()
        print()

        if choice == "1":
            _register()
        elif choice == "2":
            _delete()
        elif choice == "3" and required:
            _setup_project(required)
        elif choice == "q":
            return
        else:
            print("メニューにある番号か q を入力してください。")


def _show_names() -> None:
    registered = list_names()
    if registered:
        print("登録済みのキー名:")
        for name in registered:
            print(f"  {name}")
    else:
        print("登録済みのキー名はまだありません。")


def _register() -> None:
    prefix = input("システム名（例: salesforce）: ").strip()
    if not prefix:
        print("システム名が入力されなかったため中止しました。")
        return
    if not CREDENTIAL_NAME_PATTERN.fullmatch(prefix):
        print("システム名に使えるのは半角英数字とアンダースコアだけです（例: salesforce, oju_sys）。")
        return

    # 既存システムへの追加なら登録済み項目を表示し、
    # 新しいシステム名なら確認を挟む（既存システム名のスペルミス防止）
    registered_items = [
        n.removeprefix(f"{prefix}_") for n in list_names() if n.startswith(f"{prefix}_")
    ]
    if registered_items:
        print(f"{prefix} の登録済み項目: {', '.join(registered_items)}")
    else:
        confirm = input(f"{prefix} は新しいシステム名です。この名前で登録しますか？（y で続行）: ")
        if confirm.strip().lower() != "y":
            print("中止しました。既存のシステム名に追加する場合はスペルを確認してください。")
            return

    while True:
        item = input("項目名（例: username / password / token。空 Enter で終了）: ").strip()
        if not item:
            break
        if not CREDENTIAL_NAME_PATTERN.fullmatch(item):
            print("項目名に使えるのは半角英数字とアンダースコアだけです（例: username）。")
            continue

        name = f"{prefix}_{item}"
        if name in list_names():
            print(f"{name} は登録済みのため、上書きになります。")

        value = getpass.getpass("値（入力しても画面には表示されません）: ")
        confirm_value = getpass.getpass("値（確認のためもう一度）: ")
        if value != confirm_value:
            print("2回の入力が一致しなかったため、この項目はスキップしました。")
            continue
        if not value:
            print("値が空だったため、この項目はスキップしました。")
            continue

        save_credential(name, value)
        print(f"保存しました: {name}")

    print(f"保存先: {CREDENTIALS_PATH}")


def _read_declared_credentials(project_root: str | Path = ".") -> list[str]:
    """コード内の REQUIRED_CREDENTIALS 宣言を読み取り、必要なキー名の一覧を返す。

    プロジェクト側は使う認証情報を src/credentials.py 等でこう宣言しておく:

        REQUIRED_CREDENTIALS = {
            "SALESFORCE": ["username", "password", "token"],
            "OJU_SYS": ["password"],
        }

    - 辞書のキーは config.ini [CREDENTIALS] のキー名。実際のプレフィックスは
      config.ini から解決する（SALESFORCE = salesforce_test ならテスト用に切り替わる）
    - config.ini に該当キーがない場合はキー名を小文字にしたものをプレフィックスにする
    - 対象はカレントディレクトリ直下の .py と src/ 以下の .py
    - ファイルは import せず AST で読むだけなので、コードは実行されない
    """
    root = Path(project_root)
    files = sorted(root.glob("*.py")) + sorted(root.glob("src/**/*.py"))

    cfg = configparser.ConfigParser()
    cfg.read(root / "config.ini", encoding="utf-8")

    def resolve_prefix(key: str) -> str:
        """宣言のキー名を config.ini の [CREDENTIALS] からプレフィックスに解決する。"""
        if cfg.has_section("CREDENTIALS") and cfg.has_option("CREDENTIALS", key):
            return cfg.get("CREDENTIALS", key).strip()
        return key.lower()

    declared: dict[str, list[str]] = {}
    for file in files:
        try:
            tree = ast.parse(file.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)):
                continue
            is_target = any(
                isinstance(t, ast.Name) and t.id == "REQUIRED_CREDENTIALS" for t in node.targets
            )
            if not is_target:
                continue
            try:
                value = ast.literal_eval(node.value)
            except ValueError:
                continue
            if isinstance(value, dict):
                declared.update(value)

    names = set()
    for key, items in declared.items():
        prefix = resolve_prefix(str(key))
        for item in items:
            name = f"{prefix}_{item}"
            if CREDENTIAL_NAME_PATTERN.fullmatch(name):
                names.add(name)
    return sorted(names)


def _setup_project(required: list[str]) -> None:
    """REQUIRED_CREDENTIALS 宣言のうち、未登録のものだけを順に登録する。"""
    registered = set(list_names())

    print("このプロジェクトが使う認証情報（コード内の REQUIRED_CREDENTIALS 宣言）:")
    missing = []
    for name in required:
        if name in registered:
            print(f"  {name}: 登録済み")
        else:
            print(f"  {name}: 未登録")
            missing.append(name)

    if not missing:
        print("すべて登録済みです。値を変更したい場合は「1: 登録」で上書きしてください。")
        return

    print()
    print(f"未登録の {len(missing)} 件を順番に登録します（中断は Ctrl+C）。")
    for name in missing:
        print()
        print(f"--- {name} ---")
        value = getpass.getpass("値（入力しても画面には表示されません）: ")
        confirm_value = getpass.getpass("値（確認のためもう一度）: ")
        if value != confirm_value:
            print("2回の入力が一致しなかったため、この項目はスキップしました。")
            continue
        if not value:
            print("値が空だったため、この項目はスキップしました。")
            continue
        save_credential(name, value)
        print(f"保存しました: {name}")

    print()
    print(f"保存先: {CREDENTIALS_PATH}")


def _delete() -> None:
    name = input("削除するキー名: ").strip()
    if not name:
        print("キー名が入力されなかったため中止しました。")
        return

    confirm = input(f"{name} を削除します。よろしいですか？（y で実行）: ").strip().lower()
    if confirm != "y":
        print("中止しました。")
        return

    try:
        delete_credential(name)
        print(f"削除しました: {name}")
    except CredentialNotFoundError:
        print(f"キー名が見つかりません: {name}")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        # Ctrl+C 等で中断されたときにトレースバックを出さず静かに終わる
        print("\n中断しました。")
