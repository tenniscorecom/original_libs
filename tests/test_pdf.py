"""
pdf モジュールのテスト。

pypdf が未導入の環境では全テストをスキップする（オプションモジュールのため）。
"""

import pytest

pypdf = pytest.importorskip("pypdf", reason="pypdf 未導入（comken.pdf はオプション）")

from pypdf import PdfWriter  # noqa: E402

from comken.pdf import extract_text, merge_pdfs, page_count, split_pdf  # noqa: E402


def _make_pdf(path, pages: int = 1) -> None:
    """指定ページ数の空 PDF を作る。"""
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)  # A4
    with open(path, "wb") as f:
        writer.write(f)
    writer.close()


class TestPageCount:
    def test_returns_page_count(self, tmp_path):
        """ページ数が返ることを確認する。"""
        src = tmp_path / "doc.pdf"
        _make_pdf(src, pages=3)

        assert page_count(src) == 3


class TestMergePdfs:
    def test_merges_in_order(self, tmp_path):
        """結合後のページ数が合計と一致することを確認する。"""
        a = tmp_path / "a.pdf"
        b = tmp_path / "b.pdf"
        _make_pdf(a, pages=2)
        _make_pdf(b, pages=3)

        dst = merge_pdfs([a, b], tmp_path / "out" / "merged.pdf")

        assert page_count(dst) == 5

    def test_missing_file_raises(self, tmp_path):
        """存在しないファイルが含まれると FileNotFoundError になることを確認する。"""
        with pytest.raises(FileNotFoundError):
            merge_pdfs([tmp_path / "なし.pdf"], tmp_path / "out.pdf")


class TestSplitPdf:
    def test_splits_into_single_pages(self, tmp_path):
        """1ページずつ連番ファイルに分割されることを確認する。"""
        src = tmp_path / "請求書まとめ.pdf"
        _make_pdf(src, pages=3)

        paths = split_pdf(src)

        assert [p.name for p in paths] == [
            "請求書まとめ_001.pdf",
            "請求書まとめ_002.pdf",
            "請求書まとめ_003.pdf",
        ]
        assert all(page_count(p) == 1 for p in paths)

    def test_custom_destination_folder(self, tmp_path):
        """出力先フォルダを指定でき、自動作成されることを確認する。"""
        src = tmp_path / "doc.pdf"
        _make_pdf(src, pages=1)

        paths = split_pdf(src, tmp_path / "分割")

        assert paths[0].parent == tmp_path / "分割"


class TestExtractText:
    def test_blank_pdf_returns_empty_text(self, tmp_path):
        """文字情報のない PDF からは空のテキストが返ることを確認する（エラーにならない）。"""
        src = tmp_path / "blank.pdf"
        _make_pdf(src, pages=2)

        assert extract_text(src).strip() == ""