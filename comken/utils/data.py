"""
utils/data.py — データ変換・比較ユーティリティ

使い方:
    from comken.utils import col_to_num, diff_rows

    # Excel の列レターを列番号に変換
    col_to_num("Q")   # → 17

    # 2つのデータセットの差分
    result = diff_rows(rows_a, rows_b, key="社員番号")
    # result["added"]   → B にあって A にない行
    # result["removed"] → A にあって B にない行
    # result["changed"] → キーが一致するが値が異なる行
"""


def col_to_num(letter: str) -> int:
    """Excel の列レターを列番号に変換する（A→1, B→2, AA→27）。

    config.ini に「Q列」のように列レターで書かれた設定を、
    ExcelComHandler.read_cell() 等の col 引数（数値）に変換するときに使う。

    Args:
        letter: 列レター（大文字・小文字どちらでも可。A〜Z または AA〜ZZZ 形式）。

    Returns:
        1始まりの列番号。

    Raises:
        ValueError: 空文字列または英字以外が含まれる場合。
    """
    normalized = str(letter).strip().upper()
    if not normalized or not normalized.isalpha():
        raise ValueError(
            f"列レターとして無効な値です: {letter!r}\n"
            "A〜Z または AA〜ZZZ 形式で指定してください（例: 'A', 'Q', 'AA'）。"
        )
    result = 0
    for char in normalized:
        result = result * 26 + (ord(char) - ord("A") + 1)
    return result


def diff_rows(
    a: list[dict],
    b: list[dict],
    key: str,
) -> dict[str, list]:
    """2つのデータセットをキー列で比較し、差分を返す。

    使い方:
        rows_a = [{"社員番号": "001", "氏名": "山田"}, ...]
        rows_b = [{"社員番号": "001", "氏名": "山田太郎"}, ...]

        result = diff_rows(rows_a, rows_b, key="社員番号")
        for row in result["changed"]:
            print(row["key"], row["before"], row["after"])

    Args:
        a: 比較元のデータ（辞書のリスト）。
        b: 比較先のデータ（辞書のリスト）。
        key: 行を一意に識別するキー列名。

    Returns:
        以下のキーを持つ辞書:
        - "added":   b にあって a にない行のリスト
        - "removed": a にあって b にない行のリスト
        - "changed": 変更のある行のリスト。各要素は
                     {"key": ..., "before": {...}, "after": {...}} の形式。
    """
    a_by_key = {row[key]: row for row in a}
    b_by_key = {row[key]: row for row in b}

    added = [b_by_key[k] for k in b_by_key if k not in a_by_key]
    removed = [a_by_key[k] for k in a_by_key if k not in b_by_key]
    changed = [
        {"key": k, "before": a_by_key[k], "after": b_by_key[k]}
        for k in a_by_key
        if k in b_by_key and a_by_key[k] != b_by_key[k]
    ]

    return {"added": added, "removed": removed, "changed": changed}
