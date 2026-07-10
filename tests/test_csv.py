"""
CsvReader クラスのテスト。

実行方法:
    cd F:\\dev\\original_libs
    python -m pytest tests/ -v
"""

import pytest

from comken.csv.handler import CsvReader


@pytest.fixture
def sample_csv(tmp_path):
    """テスト用 CSV ファイルを作成して返す。"""
    content = "注文番号,金額,担当者\nA001,1000,山田\nA002,2000,山田\nA003,3000,佐藤\n"
    path = tmp_path / "data.csv"
    path.write_text(content, encoding="utf-8-sig")
    return path


class TestCsvReaderRows:
    """rows() のテスト。"""

    def test_returns_all_rows(self, sample_csv):
        """全行を辞書のリストで返すことを確認する。"""
        rows = CsvReader(sample_csv).rows()
        assert len(rows) == 3
        assert rows[0] == {"注文番号": "A001", "金額": "1000", "担当者": "山田"}

    def test_columns_filter(self, sample_csv):
        """columns 指定時は指定列のみ返すことを確認する。"""
        rows = CsvReader(sample_csv).rows(columns=["注文番号", "金額"])
        assert rows[0] == {"注文番号": "A001", "金額": "1000"}
        assert "担当者" not in rows[0]


class TestCsvReaderFind:
    """find() のテスト。"""

    def test_finds_existing_row(self, sample_csv):
        """キーに一致する行を返すことを確認する。"""
        row = CsvReader(sample_csv).find("注文番号", "A001")
        assert row is not None
        assert row["金額"] == "1000"

    def test_returns_none_when_not_found(self, sample_csv):
        """見つからない場合は None を返すことを確認する。"""
        row = CsvReader(sample_csv).find("注文番号", "Z999")
        assert row is None

    def test_returns_first_match(self, sample_csv):
        """複数一致する場合は最初の行を返すことを確認する。"""
        row = CsvReader(sample_csv).find("担当者", "山田")
        assert row["注文番号"] == "A001"


class TestCsvReaderFilter:
    """filter() のテスト。"""

    def test_returns_matching_rows(self, sample_csv):
        """条件に一致する全行を返すことを確認する。"""
        rows = CsvReader(sample_csv).filter("担当者", "山田")
        assert len(rows) == 2
        assert all(r["担当者"] == "山田" for r in rows)

    def test_returns_empty_list_when_not_found(self, sample_csv):
        """一致しない場合は空リストを返すことを確認する。"""
        rows = CsvReader(sample_csv).filter("担当者", "存在しない人")
        assert rows == []


class TestCsvReaderColumn:
    """column() のテスト。"""

    def test_returns_column_values(self, sample_csv):
        """指定列の値一覧を返すことを確認する。"""
        values = CsvReader(sample_csv).column("金額")
        assert values == ["1000", "2000", "3000"]


class TestCsvReaderIndex:
    """index() のテスト。"""

    def test_returns_dict_keyed_by_column(self, sample_csv):
        """キー列で辞書化されることを確認する。"""
        lookup = CsvReader(sample_csv).index("注文番号")
        assert "A001" in lookup
        assert lookup["A001"]["金額"] == "1000"

    def test_all_rows_indexed(self, sample_csv):
        """全行がインデックスに含まれることを確認する。"""
        lookup = CsvReader(sample_csv).index("注文番号")
        assert len(lookup) == 3


class TestCsvReaderEncoding:
    """文字コードのテスト。"""

    def test_reads_cp932(self, tmp_path):
        """Shift-JIS（cp932）のファイルを読み込めることを確認する。"""
        path = tmp_path / "sjis.csv"
        path.write_bytes("番号,名前\n1,山田\n".encode("cp932"))
        rows = CsvReader(path, encoding="cp932").rows()
        assert rows[0]["名前"] == "山田"
