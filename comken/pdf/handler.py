"""
pdf/handler.py — PDF ユーティリティ（pypdf ベース）

PDF の結合・分割・テキスト抽出・ページ数取得。

※ pypdf（外部ライブラリ）が必要。導入できない環境ではこのフォルダ（comken/pdf）は使えない
  （import した時点で対処法つきのエラーになる。他のモジュールには影響しない）。

使い方:
    from comken.pdf import extract_text, merge_pdfs, page_count, split_pdf

    # 結合
    merge_pdfs(["表紙.pdf", "本文.pdf"], r"C:\\作業\\提出用.pdf")

    # 1ページずつ分割
    paths = split_pdf(r"C:\\作業\\請求書まとめ.pdf")   # → 請求書まとめ_001.pdf, _002.pdf ...

    # テキスト抽出・ページ数
    text = extract_text("報告書.pdf")
    n = page_count("報告書.pdf")
"""

from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError as e:
    raise ImportError(
        "comken.pdf を使うには pypdf が必要です: pip install pypdf\n"
        "（外部ライブラリを導入できない環境では PDF 機能は使えません）"
    ) from e


def merge_pdfs(files: list, dst: str | Path) -> Path:
    """複数の PDF を1つに結合する（files の順に並ぶ）。

    Args:
        files: 結合する PDF のパスのリスト。
        dst: 出力する PDF のパス。親フォルダがなければ自動作成される。

    Returns:
        作成した PDF のパス。

    Raises:
        FileNotFoundError: files の中に存在しないファイルがある場合。
    """
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)

    writer = PdfWriter()
    for file in files:
        file = Path(file)
        if not file.is_file():
            raise FileNotFoundError(f"PDF が見つかりません: {file}")
        writer.append(str(file))
    with open(dst, "wb") as f:
        writer.write(f)
    writer.close()
    return dst


def split_pdf(src: str | Path, dst_folder: str | Path | None = None) -> list[Path]:
    """PDF を1ページずつ別ファイルに分割する。

    Args:
        src: 分割する PDF のパス。
        dst_folder: 出力先フォルダ。省略すると src と同じフォルダ。
                    ファイル名は「元の名前_001.pdf」の連番になる。

    Returns:
        作成した PDF のパスのリスト（ページ順）。
    """
    src = Path(src)
    dst_folder = Path(dst_folder) if dst_folder else src.parent
    dst_folder.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(src))
    paths = []
    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        path = dst_folder / f"{src.stem}_{i:03d}.pdf"
        with open(path, "wb") as f:
            writer.write(f)
        writer.close()
        paths.append(path)
    return paths


def extract_text(src: str | Path) -> str:
    """PDF の全ページのテキストを取り出す（ページ間は改行で区切る）。

    スキャン画像だけの PDF（文字情報がないもの）からは空文字列が返る。

    Args:
        src: PDF のパス。

    Returns:
        抽出したテキスト。
    """
    reader = PdfReader(str(src))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def page_count(src: str | Path) -> int:
    """PDF のページ数を返す。

    Args:
        src: PDF のパス。
    """
    return len(PdfReader(str(src)).pages)
