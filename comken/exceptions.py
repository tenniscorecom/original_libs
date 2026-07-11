"""
exceptions.py — ライブラリ共通の例外クラス

すべての例外は OriginalLibsError を継承しているため、
まとめて補足したい場合は except OriginalLibsError で受けられる。

使い方:
    from comken.exceptions import SheetNotFoundError, ColumnNotFoundError

    try:
        with ExcelFile("data.xlsx") as f:
            rows = f.read_rows_as_dicts("存在しないシート")
    except SheetNotFoundError as e:
        print(e)  # → "シートが見つかりません: 存在しないシート ..."
"""


class OriginalLibsError(Exception):
    """ライブラリ共通の基底例外。"""


class ExcelError(OriginalLibsError):
    """Excel 操作に関する例外の基底クラス。"""


class SheetNotFoundError(ExcelError):
    """指定したシートが存在しない場合。

    発生箇所: ExcelFile.sheet() / ExcelComHandler.sheet()
    """


class MacroError(ExcelError):
    """VBA マクロの実行に失敗した場合。

    発生箇所: ExcelFile.run_macro() / ExcelComHandler.run_macro()
    """


class ColumnNotFoundError(OriginalLibsError):
    """期待するカラムが見つからない場合（Excel・CSV 共通）。

    非エンジニアが列名を変更したときに分かりやすいメッセージを出すために使う。

    使い方:
        from comken.exceptions import ColumnNotFoundError

        REQUIRED_COLUMNS = ["日付", "担当者", "金額"]

        def validate_columns(rows: list[dict], required: list[str]) -> None:
            missing = set(required) - set(rows[0].keys())
            if missing:
                raise ColumnNotFoundError(
                    f"Excelのヘッダーが正しくありません。\\n"
                    f"見つからない列: {', '.join(missing)}\\n"
                    f"Excelの1行目を確認してください。"
                )
    """


class CsvError(OriginalLibsError):
    """CSV 操作に関する例外の基底クラス。"""


class ConfigError(OriginalLibsError):
    """設定ファイルに関する例外。

    発生箇所: Config クラスで必須キーが存在しない場合など。
    """


class SalesforceError(OriginalLibsError):
    """Salesforce API の呼び出しに失敗した場合。

    発生箇所: SalesforceApiClient の各メソッド

    ログイン失敗・API エラー・Bulk ジョブ失敗など。
    メッセージに HTTP ステータスや Salesforce からのエラー詳細を含める。
    """


class CredentialError(OriginalLibsError):
    """認証情報の保存・取得に関する例外の基底クラス。"""


class CredentialNotFoundError(CredentialError):
    """指定したサービス名の認証情報が登録されていない場合。

    発生箇所: credentials.load_credential()

    非エンジニアにも分かるよう、登録コマンド（python -m comken.credentials)
    を案内するメッセージを含めている。
    """


class InvalidCredentialNameError(CredentialError):
    """キー名に使えない文字が含まれている場合。

    発生箇所: credentials.save_credential()

    キー名に使えるのは半角英数字とアンダースコアのみ。
    漢字・スペース・記号を含む名前はコードや config.ini に書きにくいため弾く。
    """
