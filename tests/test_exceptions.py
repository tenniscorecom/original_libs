"""
例外クラスのテスト。

実行方法:
    リポジトリのルートで python -m pytest tests/ -v
"""

import warnings

import pytest

from comken.exceptions import (
    ColumnNotFoundError,
    ConfigError,
    CsvError,
    ExcelError,
    MacroError,
    OriginalLibsError,
    SheetNotFoundError,
    _warn_coerce,
)


class TestExceptionHierarchy:
    """例外の継承関係のテスト。

    すべての例外が正しく OriginalLibsError を継承しているかを確認する。
    継承関係が正しいと、except OriginalLibsError でまとめて補足できる。
    """

    def test_sheet_not_found_is_excel_error(self):
        """SheetNotFoundError は ExcelError のサブクラスである。"""
        assert issubclass(SheetNotFoundError, ExcelError)

    def test_macro_error_is_excel_error(self):
        """MacroError は ExcelError のサブクラスである。"""
        assert issubclass(MacroError, ExcelError)

    def test_excel_error_is_original_libs_error(self):
        """ExcelError は OriginalLibsError のサブクラスである。"""
        assert issubclass(ExcelError, OriginalLibsError)

    def test_column_not_found_is_original_libs_error(self):
        """ColumnNotFoundError は OriginalLibsError のサブクラスである。"""
        assert issubclass(ColumnNotFoundError, OriginalLibsError)

    def test_csv_error_is_original_libs_error(self):
        """CsvError は OriginalLibsError のサブクラスである。"""
        assert issubclass(CsvError, OriginalLibsError)

    def test_config_error_is_original_libs_error(self):
        """ConfigError は OriginalLibsError のサブクラスである。"""
        assert issubclass(ConfigError, OriginalLibsError)


class TestExceptionMessages:
    """例外メッセージのテスト。

    非エンジニアが読んでも分かるメッセージになっているかを確認する。
    """

    def test_sheet_not_found_message(self):
        """SheetNotFoundError のメッセージに存在しないシート名が含まれる。"""
        with pytest.raises(SheetNotFoundError, match="Sheet2"):
            raise SheetNotFoundError("シートが見つかりません: Sheet2")

    def test_column_not_found_message(self):
        """ColumnNotFoundError のメッセージにヘッダー確認を促す文言が含まれる。"""
        missing = {"金額", "担当者"}
        with pytest.raises(ColumnNotFoundError, match="Excelのヘッダー"):
            raise ColumnNotFoundError(
                f"Excelのヘッダーが正しくありません。\n"
                f"見つからない列: {', '.join(missing)}\n"
                f"Excelの1行目を確認してください。"
            )

    def test_catch_by_base_class(self):
        """OriginalLibsError でサブクラスの例外をまとめて補足できる。

        プロジェクト側で except OriginalLibsError と書けば、
        ライブラリ内で発生したすべての例外を一箇所で処理できる。
        """
        with pytest.raises(OriginalLibsError):
            raise SheetNotFoundError("テスト")

        with pytest.raises(OriginalLibsError):
            raise ColumnNotFoundError("テスト")

        with pytest.raises(OriginalLibsError):
            raise MacroError("テスト")


class TestWarnCoerce:
    """_warn_coerce のテスト。"""

    def test_none_raises_type_error(self):
        """None を渡すと TypeError が発生することを確認する。"""
        with pytest.raises(TypeError, match="None"):
            _warn_coerce(None, str, "sheet_name")

    def test_wrong_type_warns_and_converts(self):
        """型が違う場合に UserWarning を発行して変換することを確認する。"""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = _warn_coerce(1, str, "sheet_name")
        assert result == "1"
        assert isinstance(result, str)
        assert len(caught) == 1
        assert issubclass(caught[0].category, UserWarning)

    def test_correct_type_no_warning(self):
        """型が一致している場合は警告なしでそのまま返すことを確認する。"""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = _warn_coerce("ok", str, "sheet_name")
        assert result == "ok"
        assert len(caught) == 0
