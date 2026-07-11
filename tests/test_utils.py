"""
utils モジュールのテスト。

実行方法:
    cd F:\\dev\\original_libs
    python -m pytest tests/ -v
"""

import datetime
import os

import pytest

from comken.utils import (
    DownloadDir,
    FileFinder,
    FileNameBuilder,
    SortBy,
    col_to_num,
    copy_file,
    move_file,
)


class TestMoveFile:
    """move_file のテスト。"""

    def test_moves_into_existing_folder(self, tmp_path):
        """dst が既存フォルダなら、その中に同名で移動する。"""
        src = tmp_path / "report.xlsx"
        src.write_text("data", encoding="utf-8")
        folder = tmp_path / "output"
        folder.mkdir()

        result = move_file(src, folder)

        assert result == folder / "report.xlsx"
        assert result.read_text(encoding="utf-8") == "data"
        assert not src.exists()

    def test_moves_to_file_path_with_auto_mkdir(self, tmp_path):
        """ファイルパス指定なら親フォルダを自動作成して移動する。"""
        src = tmp_path / "report.xlsx"
        src.write_text("data", encoding="utf-8")
        target = tmp_path / "out" / "sub" / "売上.xlsx"

        result = move_file(src, target)

        assert result == target
        assert target.exists()

    def test_overwrites_existing_file(self, tmp_path):
        """移動先に同名ファイルがあれば上書きする。"""
        src = tmp_path / "report.xlsx"
        src.write_text("new", encoding="utf-8")
        target = tmp_path / "out" / "report.xlsx"
        target.parent.mkdir()
        target.write_text("old", encoding="utf-8")

        move_file(src, target)

        assert target.read_text(encoding="utf-8") == "new"


class TestCopyFile:
    """copy_file のテスト。"""

    def test_copies_into_existing_folder(self, tmp_path):
        """dst が既存フォルダなら、その中に同名でコピーする（元は残る）。"""
        src = tmp_path / "report.xlsx"
        src.write_text("data", encoding="utf-8")
        folder = tmp_path / "output"
        folder.mkdir()

        result = copy_file(src, folder)

        assert result == folder / "report.xlsx"
        assert src.exists()  # 元ファイルは残る

    def test_copies_to_file_path_with_auto_mkdir(self, tmp_path):
        """ファイルパス指定なら親フォルダを自動作成してコピーする。"""
        src = tmp_path / "report.xlsx"
        src.write_text("data", encoding="utf-8")
        target = tmp_path / "out" / "backup.xlsx"

        result = copy_file(src, target)

        assert result == target
        assert target.read_text(encoding="utf-8") == "data"


class TestColToNum:
    """col_to_num のテスト。Excel の列レターを列番号に変換する。"""

    @pytest.mark.parametrize(
        ("letter", "expected"),
        [("A", 1), ("B", 2), ("Q", 17), ("Z", 26), ("AA", 27), ("AZ", 52)],
    )
    def test_converts_letter_to_number(self, letter, expected):
        """列レターが正しい列番号に変換されることを確認する。"""
        assert col_to_num(letter) == expected

    def test_lowercase_is_allowed(self):
        """小文字でも変換できることを確認する。"""
        assert col_to_num("q") == 17


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

    def test_raises_when_not_found(self, tmp_path):
        """今日の日付を含むファイルが存在しない場合は FileNotFoundError になる。"""
        (tmp_path / "20200101_古いファイル.xlsx").touch()

        with pytest.raises(FileNotFoundError):
            FileFinder(tmp_path).today()

    def test_returns_none_when_not_required(self, tmp_path):
        """required=False なら見つからなくても None を返す。"""
        assert FileFinder(tmp_path).today(required=False) is None

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

    デフォルトはファイル名の辞書順で最後のファイルを取得する。
    """

    def test_finds_latest_by_name(self, tmp_path):
        """ファイル名の辞書順で最後のファイルを返す（更新日時は影響しない）。"""
        name_new = tmp_path / "20260711_売上.xlsx"
        name_old = tmp_path / "20260101_売上.xlsx"
        name_new.touch()
        name_old.touch()
        os.utime(name_new, (0, 0))  # 名前上の最新の方を、更新日時では最古にする

        assert FileFinder(tmp_path).latest() == name_new

    def test_finds_latest_by_updated(self, tmp_path):
        """by="updated" なら更新日時が最も新しいファイルを返す。"""
        name_new = tmp_path / "20260711_売上.xlsx"
        name_old = tmp_path / "20260101_売上.xlsx"
        name_new.touch()
        name_old.touch()
        os.utime(name_new, (0, 0))  # 名前上の最新の方を、更新日時では最古にする

        assert FileFinder(tmp_path).latest(by=SortBy.UPDATED) == name_old

    def test_invalid_by_raises(self, tmp_path):
        """by に不正な値を指定すると ValueError になる。"""
        with pytest.raises(ValueError):
            FileFinder(tmp_path).latest(by="date")

    def test_raises_when_empty(self, tmp_path):
        """対象ファイルが存在しない場合は FileNotFoundError になる。"""
        with pytest.raises(FileNotFoundError):
            FileFinder(tmp_path).latest()

    def test_returns_none_when_not_required(self, tmp_path):
        """required=False なら見つからなくても None を返す。"""
        assert FileFinder(tmp_path).latest(required=False) is None

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

    def test_with_block_auto_removes_temp_dir(self):
        """with を抜けると一時フォルダは自動削除される（消し忘れ防止）。"""
        with DownloadDir() as dl:
            assert dl.path.is_dir()

        assert not dl.path.exists()

    def test_with_block_keeps_specified_path(self, tmp_path):
        """path 指定した固定フォルダは with を抜けても削除されない。"""
        target = tmp_path / "downloads"
        with DownloadDir(path=target) as dl:
            (dl.path / "report.xlsx").touch()

        assert target.exists()
        assert (target / "report.xlsx").exists()

    def test_uses_specified_path(self, tmp_path):
        """path 指定で既存フォルダをそのまま使えることを確認する。"""
        target = tmp_path / "downloads"

        dl = DownloadDir(path=target)

        assert dl.path == target
        assert target.is_dir()  # なければ作成される

    def test_wait_ignores_preexisting_files(self, tmp_path):
        """path 指定時、作成前からあったファイルは完了対象にならないことを確認する。"""
        old_file = tmp_path / "前回のダウンロード.xlsx"
        old_file.touch()

        dl = DownloadDir(path=tmp_path)
        new_file = tmp_path / "今回のダウンロード.xlsx"
        new_file.touch()

        assert dl.wait(timeout=3) == [new_file]

    def test_wait_times_out_when_only_old_files(self, tmp_path):
        """path 指定時、前回のファイルしかなければタイムアウトすることを確認する。"""
        (tmp_path / "前回のダウンロード.xlsx").touch()

        dl = DownloadDir(path=tmp_path)

        with pytest.raises(TimeoutError):
            dl.wait(timeout=1)

    def test_remove_skips_specified_path_with_warning(self, tmp_path, caplog):
        """path 指定した固定フォルダは remove() で削除されず、警告が出ることを確認する。"""
        target = tmp_path / "downloads"
        dl = DownloadDir(path=target)

        dl.remove()

        assert target.exists()
        assert "削除しません" in caplog.text

    def test_remove_force_deletes_specified_path(self, tmp_path):
        """force=True なら path 指定した固定フォルダも削除されることを確認する。"""
        target = tmp_path / "downloads"
        dl = DownloadDir(path=target)

        dl.remove(force=True)

        assert not target.exists()
