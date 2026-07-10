"""
utils モジュールのテスト。

実行方法:
    cd F:\\dev\\original_libs
    python -m pytest tests/ -v
"""

import datetime
import os
from pathlib import Path

import pytest

from comken.utils import dated_filename, find_latest_file, find_today_file


class TestDatedFilename:
    """dated_filename のテスト。

    今日の日付をファイル名に付与する関数。
    プレフィックス・サフィックス・日付フォーマットの組み合わせを確認する。
    """

    def test_default_prefix(self):
        """デフォルトでは YYYYMMDD がプレフィックスになる。"""
        today = datetime.date.today().strftime("%Y%m%d")
        assert dated_filename("レポート") == f"{today}_レポート.xlsx"

    def test_suffix_mode(self):
        """pre=False にすると日付がサフィックスになる。"""
        today = datetime.date.today().strftime("%Y%m%d")
        assert dated_filename("レポート", pre=False) == f"レポート_{today}.xlsx"

    def test_custom_suffix(self):
        """suffix 引数で拡張子を変更できる。"""
        today = datetime.date.today().strftime("%Y%m%d")
        assert dated_filename("ログ", suffix=".csv") == f"{today}_ログ.csv"

    def test_yyyymm_format(self):
        """date_format="%Y%m" にすると年月のみになる。月次ファイルに使う。"""
        ym = datetime.date.today().strftime("%Y%m")
        assert dated_filename("月次", date_format="%Y%m") == f"{ym}_月次.xlsx"

    def test_custom_date_format(self):
        """任意の strftime フォーマットを指定できる。"""
        formatted = datetime.date.today().strftime("%Y-%m-%d")
        assert dated_filename("レポート", date_format="%Y-%m-%d") == f"{formatted}_レポート.xlsx"


class TestFindTodayFile:
    """find_today_file のテスト。

    フォルダ内から今日の日付を含むファイルを取得する関数。
    tmp_path は pytest が提供するテスト用の一時フォルダで、テスト後に自動削除される。
    """

    def test_finds_today_file(self, tmp_path):
        """今日の日付を含むファイルが見つかる。"""
        today = datetime.date.today().strftime("%Y%m%d")
        target = tmp_path / f"{today}_売上.xlsx"
        target.touch()

        result = find_today_file(tmp_path)
        assert result == target

    def test_returns_none_when_not_found(self, tmp_path):
        """今日の日付を含むファイルが存在しない場合は None を返す。"""
        (tmp_path / "20200101_古いファイル.xlsx").touch()
        assert find_today_file(tmp_path) is None

    def test_yyyymm_format(self, tmp_path):
        """date_format="%Y%m" で年月のみのファイル名を検索できる。"""
        ym = datetime.date.today().strftime("%Y%m")
        target = tmp_path / f"{ym}_月次.xlsx"
        target.touch()

        result = find_today_file(tmp_path, date_format="%Y%m")
        assert result == target

    def test_csv_pattern(self, tmp_path):
        """pattern="*.csv" にすると CSV ファイルのみ検索対象になる。"""
        today = datetime.date.today().strftime("%Y%m%d")
        target = tmp_path / f"{today}_ログ.csv"
        target.touch()

        result = find_today_file(tmp_path, pattern="*.csv")
        assert result == target

    def test_returns_latest_when_multiple(self, tmp_path):
        """今日のファイルが複数ある場合、更新日時が最も新しいものを返す。"""
        today = datetime.date.today().strftime("%Y%m%d")
        old = tmp_path / f"{today}_v1.xlsx"
        new = tmp_path / f"{today}_v2.xlsx"
        old.touch()
        new.touch()
        os.utime(old, (0, 0)) # old の更新日時を過去（Unix エポック）に設定

        result = find_today_file(tmp_path)
        assert result == new


class TestFindLatestFile:
    """find_latest_file のテスト。

    フォルダ内から更新日時が最も新しいファイルを取得する関数。
    """

    def test_finds_latest(self, tmp_path):
        """更新日時が最も新しいファイルを返す。"""
        old = tmp_path / "20260101_old.xlsx"
        new = tmp_path / "20260710_new.xlsx"
        old.touch()
        new.touch()
        os.utime(old, (0, 0)) # old の更新日時を過去に設定

        assert find_latest_file(tmp_path) == new

    def test_returns_none_when_empty(self, tmp_path):
        """対象ファイルが存在しない場合は None を返す。"""
        assert find_latest_file(tmp_path) is None

    def test_csv_pattern(self, tmp_path):
        """pattern="*.csv" で CSV のみ対象にできる。xlsx は無視される。"""
        (tmp_path / "data.xlsx").touch()
        target = tmp_path / "data.csv"
        target.touch()

        assert find_latest_file(tmp_path, pattern="*.csv") == target
