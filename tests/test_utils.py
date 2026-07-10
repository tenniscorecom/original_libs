"""
utils モジュールのテスト。

実行方法:
    cd F:\\dev\\original_libs
    python -m pytest tests/ -v
"""

import datetime
import os

import pytest

from comken.utils import DownloadDir, FileFinder, FileNameBuilder


class TestFileNameBuilder:
    """FileNameBuilder のテスト。

    今日の日付をファイル名に付与するクラス。
    prefix / suffix / 拡張子 / 日付フォーマットの組み合わせを確認する。
    """

    def test_plain(self):
        """plain() は日付なしのファイル名を返す。"""
        assert FileNameBuilder("レポート").plain() == "レポート.xlsx"

    def test_prefix(self):
        """prefix() は YYYYMMDD を前に付ける。"""
        today = datetime.date.today().strftime("%Y%m%d")
        assert FileNameBuilder("レポート").prefix() == f"{today}_レポート.xlsx"

    def test_suffix(self):
        """suffix() は YYYYMMDD を後ろに付ける。"""
        today = datetime.date.today().strftime("%Y%m%d")
        assert FileNameBuilder("レポート").suffix() == f"レポート_{today}.xlsx"

    def test_custom_ext(self):
        """ext 引数で拡張子を変更できる。"""
        today = datetime.date.today().strftime("%Y%m%d")
        assert FileNameBuilder("ログ", ext=".csv").prefix() == f"{today}_ログ.csv"

    def test_yyyymm_format(self):
        """date_format="%Y%m" にすると年月のみになる。月次ファイルに使う。"""
        ym = datetime.date.today().strftime("%Y%m")
        assert FileNameBuilder("月次").prefix(date_format="%Y%m") == f"{ym}_月次.xlsx"

    def test_custom_date_format(self):
        """任意の strftime フォーマットを指定できる。"""
        formatted = datetime.date.today().strftime("%Y-%m-%d")
        assert FileNameBuilder("レポート").prefix(date_format="%Y-%m-%d") == f"{formatted}_レポート.xlsx"


class TestFileFinderToday:
    """FileFinder.today() のテスト。

    フォルダ内から今日の日付を含むファイルを取得する。
    tmp_path は pytest が提供するテスト用の一時フォルダで、テスト後に自動削除される。
    """

    def test_finds_today_file(self, tmp_path):
        """今日の日付を含むファイルが見つかる。"""
        today = datetime.date.today().strftime("%Y%m%d")
        target = tmp_path / f"{today}_売上.xlsx"
        target.touch()

        assert FileFinder(tmp_path).today() == target

    def test_returns_none_when_not_found(self, tmp_path):
        """今日の日付を含むファイルが存在しない場合は None を返す。"""
        (tmp_path / "20200101_古いファイル.xlsx").touch()
        assert FileFinder(tmp_path).today() is None

    def test_yyyymm_format(self, tmp_path):
        """date_format="%Y%m" で年月のみのファイル名を検索できる。"""
        ym = datetime.date.today().strftime("%Y%m")
        target = tmp_path / f"{ym}_月次.xlsx"
        target.touch()

        assert FileFinder(tmp_path).today(date_format="%Y%m") == target

    def test_csv_pattern(self, tmp_path):
        """pattern="*.csv" にすると CSV ファイルのみ検索対象になる。"""
        today = datetime.date.today().strftime("%Y%m%d")
        target = tmp_path / f"{today}_ログ.csv"
        target.touch()

        assert FileFinder(tmp_path).today(pattern="*.csv") == target

    def test_returns_latest_when_multiple(self, tmp_path):
        """今日のファイルが複数ある場合、更新日時が最も新しいものを返す。"""
        today = datetime.date.today().strftime("%Y%m%d")
        old = tmp_path / f"{today}_v1.xlsx"
        new = tmp_path / f"{today}_v2.xlsx"
        old.touch()
        new.touch()
        os.utime(old, (0, 0))  # old の更新日時を過去（Unix エポック）に設定

        assert FileFinder(tmp_path).today() == new


class TestFileFinderLatest:
    """FileFinder.latest() のテスト。

    フォルダ内から更新日時が最も新しいファイルを取得する。
    """

    def test_finds_latest(self, tmp_path):
        """更新日時が最も新しいファイルを返す。"""
        old = tmp_path / "20260101_old.xlsx"
        new = tmp_path / "20260711_new.xlsx"
        old.touch()
        new.touch()
        os.utime(old, (0, 0))  # old の更新日時を過去に設定

        assert FileFinder(tmp_path).latest() == new

    def test_returns_none_when_empty(self, tmp_path):
        """対象ファイルが存在しない場合は None を返す。"""
        assert FileFinder(tmp_path).latest() is None

    def test_csv_pattern(self, tmp_path):
        """pattern="*.csv" で CSV のみ対象にできる。xlsx は無視される。"""
        (tmp_path / "data.xlsx").touch()
        target = tmp_path / "data.csv"
        target.touch()

        assert FileFinder(tmp_path).latest(pattern="*.csv") == target


class TestDownloadDir:
    """DownloadDir のテスト。

    ブラウザダウンロード用の一時フォルダの作成・完了待ち・削除を確認する。
    """

    def test_creates_temp_dir(self):
        """インスタンス化すると一時フォルダが作成される。"""
        dl = DownloadDir()
        try:
            assert dl.path.is_dir()
        finally:
            dl.remove()

    def test_fspath_allows_path_conversion(self):
        """os.PathLike として Path() にそのまま渡せる。"""
        from pathlib import Path

        dl = DownloadDir()
        try:
            assert Path(dl) == dl.path
        finally:
            dl.remove()

    def test_wait_returns_completed_files(self):
        """ダウンロード中ファイルがなければ、完了ファイルの一覧を返す。"""
        dl = DownloadDir()
        try:
            target = dl.path / "report.xlsx"
            target.touch()

            assert dl.wait(timeout=3) == [target]
        finally:
            dl.remove()

    def test_wait_times_out_when_in_progress(self):
        """.crdownload が残っている間は完了とみなさず、タイムアウトする。"""
        dl = DownloadDir()
        try:
            (dl.path / "report.xlsx.crdownload").touch()

            with pytest.raises(TimeoutError):
                dl.wait(timeout=1)
        finally:
            dl.remove()

    def test_remove_deletes_dir(self):
        """remove() でフォルダごと削除される。"""
        dl = DownloadDir()
        dl.remove()

        assert not dl.path.exists()
