"""
utils/data.py — データ比較ユーティリティ

使い方:
    from comken.utils import diff_rows

    rows_a = reader_a.read_rows_as_dicts("Sheet1")
    rows_b = reader_b.read_rows_as_dicts("Sheet1")

    result = diff_rows(rows_a, rows_b, key="社員番号")
    # result["added"]   → B にあって A にない行
    # result["removed"] → A にあって B にない行
    # result["changed"] → キーが一致するが値が異なる行
"""


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
