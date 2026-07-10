"""
utils モジュールのテスト。

実行方法:
    cd F:\\dev\\original_libs
    python -m pytest tests/ -v
"""

import datetime
from pathlib import Path

import pytest

from src.utils import dated_filename, find_latest_file, find_today_file


class TestDatedFilename:

    def test_default_prefix(self):
        today = datetime.date.today().strftime("%Y%m%d")
        assert dated_filename("レポート") == f"{today}_レポート.xlsx"

    def test_suffix_mode(self):
        today = datetime.date.today().strftime("%Y%m%d")
        assert dated_filename("レポート", pre=False) == f"レポート_{today}.xlsx"

    def test_custom_suffix(self):
        today = datetime.date.today().strftime("%Y%m%d")
        assert dated_filename("ログ", suffix=".csv") == f"{today}_ログ.csv"

    def test_yyyymm_format(self):
        ym = datetime.date.today().strftime("%Y%m")
        assert dated_filename("月次", date_format="%Y%m") == f"{ym}_月次.xlsx"

    def test_custom_date_format(self):
        formatted = datetime.date.today().strftime("%Y-%m-%d")
        assert dated_filename("レポート", date_format="%Y-%m-%d") == f"{formatted}_レポート.xlsx"


class TestFindTodayFile:

    def test_finds_today_file(self, tmp_path):
        today = datetime.date.today().strftime("%Y%m%d")
        target = tmp_path / f"{today}_売上.xlsx"
        target.touch()

        result = find_today_file(tmp_path)
        assert result == target

    def test_returns_none_when_not_found(self, tmp_path):
        (tmp_path / "20200101_古いファイル.xlsx").touch()
        assert find_today_file(tmp_path) is None

    def test_yyyymm_format(self, tmp_path):
        ym = datetime.date.today().strftime("%Y%m")
        target = tmp_path / f"{ym}_月次.xlsx"
        target.touch()

        result = find_today_file(tmp_path, date_format="%Y%m")
        assert result == target

    def test_csv_pattern(self, tmp_path):
        today = datetime.date.today().strftime("%Y%m%d")
        target = tmp_path / f"{today}_ログ.csv"
        target.touch()

        result = find_today_file(tmp_path, pattern="*.csv")
        assert result == target

    def test_returns_latest_when_multiple(self, tmp_path):
        import os
        today = datetime.date.today().strftime("%Y%m%d")
        old = tmp_path / f"{today}_v1.xlsx"
        new = tmp_path / f"{today}_v2.xlsx"
        old.touch()
        new.touch()
        os.utime(old, (0, 0)) # old を過去に設定

        result = find_today_file(tmp_path)
        assert result == new


class TestFindLatestFile:

    def test_finds_latest(self, tmp_path):
        import os
        old = tmp_path / "20260101_old.xlsx"
        new = tmp_path / "20260710_new.xlsx"
        old.touch()
        new.touch()
        os.utime(old, (0, 0)) # old を過去に設定

        assert find_latest_file(tmp_path) == new

    def test_returns_none_when_empty(self, tmp_path):
        assert find_latest_file(tmp_path) is None

    def test_csv_pattern(self, tmp_path):
        (tmp_path / "data.xlsx").touch()
        target = tmp_path / "data.csv"
        target.touch()

        assert find_latest_file(tmp_path, pattern="*.csv") == target
