"""
例外クラスのテスト。

実行方法:
    cd F:\\dev\\original_libs
    python -m pytest tests/ -v
"""

import pytest

from src.exceptions import (
    ColumnNotFoundError,
    ConfigError,
    CsvError,
    ExcelError,
    MacroError,
    OriginalLibsError,
    SheetNotFoundError,
)


class TestExceptionHierarchy:
    """例外の継承関係のテスト。"""

    def test_sheet_not_found_is_excel_error(self):
        assert issubclass(SheetNotFoundError, ExcelError)

    def test_macro_error_is_excel_error(self):
        assert issubclass(MacroError, ExcelError)

    def test_excel_error_is_original_libs_error(self):
        assert issubclass(ExcelError, OriginalLibsError)

    def test_column_not_found_is_original_libs_error(self):
        assert issubclass(ColumnNotFoundError, OriginalLibsError)

    def test_csv_error_is_original_libs_error(self):
        assert issubclass(CsvError, OriginalLibsError)

    def test_config_error_is_original_libs_error(self):
        assert issubclass(ConfigError, OriginalLibsError)


class TestExceptionMessages:
    """例外メッセージのテスト。"""

    def test_sheet_not_found_message(self):
        with pytest.raises(SheetNotFoundError, match="Sheet2"):
            raise SheetNotFoundError("シートが見つかりません: Sheet2")

    def test_column_not_found_message(self):
        missing = {"金額", "担当者"}
        with pytest.raises(ColumnNotFoundError, match="Excelのヘッダー"):
            raise ColumnNotFoundError(
                f"Excelのヘッダーが正しくありません。\n"
                f"見つからない列: {', '.join(missing)}\n"
                f"Excelの1行目を確認してください。"
            )

    def test_catch_by_base_class(self):
        """OriginalLibsError でまとめて補足できることを確認。"""
        with pytest.raises(OriginalLibsError):
            raise SheetNotFoundError("テスト")

        with pytest.raises(OriginalLibsError):
            raise ColumnNotFoundError("テスト")

        with pytest.raises(OriginalLibsError):
            raise MacroError("テスト")
