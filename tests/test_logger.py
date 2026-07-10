"""logger モジュールのテスト。

ルートロガーを触るため、各テストの後にハンドラを外して他のテストに影響させない。
"""

import logging

import pytest

from comken import setup_logger


@pytest.fixture(autouse=True)
def cleanup_root_logger():
    """テスト後にルートロガーのハンドラをすべて外す。"""
    yield
    root = logging.getLogger()
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)


class TestSetupLogger:
    def test_creates_daily_log_file(self, tmp_path):
        """logs フォルダに日別のログファイルが作られることを確認する。"""
        logger = setup_logger("main", log_dir=tmp_path)
        logger.info("テストメッセージ")

        files = list(tmp_path.glob("main_*.log"))
        assert len(files) == 1

    def test_writes_message_to_file(self, tmp_path):
        """ログメッセージがファイルに書き込まれることを確認する。"""
        logger = setup_logger("main", log_dir=tmp_path)
        logger.info("処理開始")
        logging.shutdown()

        log_file = next(tmp_path.glob("main_*.log"))
        assert "処理開始" in log_file.read_text(encoding="utf-8")

    def test_submodule_logger_writes_to_same_file(self, tmp_path):
        """getLogger(__name__) のサブモジュールログも同じファイルに出ることを確認する。"""
        setup_logger("main", log_dir=tmp_path)
        logging.getLogger("src.csv_merger").info("サブモジュールから")
        logging.shutdown()

        log_file = next(tmp_path.glob("main_*.log"))
        assert "サブモジュールから" in log_file.read_text(encoding="utf-8")

    def test_no_duplicate_handlers_when_called_twice(self, tmp_path):
        """2回呼んでもハンドラが重複しない（ログが2重に出ない）ことを確認する。"""
        setup_logger("main", log_dir=tmp_path)
        logger = setup_logger("main", log_dir=tmp_path)
        logger.info("1回だけ出るはず")
        logging.shutdown()

        log_file = next(tmp_path.glob("main_*.log"))
        assert log_file.read_text(encoding="utf-8").count("1回だけ出るはず") == 1
