"""
credentials GUI のテスト。

GUI そのものの操作テストは行わず、
純粋ロジック（キー名の組み立て・分解）と画面が起動できること（スモーク）を確認する。
"""

import pytest

from comken.credentials.gui import split_name, validate_and_build_name


class TestValidateAndBuildName:
    """validate_and_build_name（フォーム入力の検証とキー名の組み立て）のテスト。"""

    def test_builds_name(self):
        """正しい入力からキー名が組み立てられる。"""
        name, error = validate_and_build_name("salesforce", "password")
        assert name == "salesforce_password"
        assert error is None

    def test_strips_whitespace(self):
        """前後の空白は除去される（コピペ時の混入対策）。"""
        name, _ = validate_and_build_name(" salesforce ", " token ")
        assert name == "salesforce_token"

    def test_empty_prefix_returns_error(self):
        """システム名が空ならエラーメッセージが返る。"""
        name, error = validate_and_build_name("", "password")
        assert name is None
        assert "システム名" in error

    def test_empty_item_returns_error(self):
        """項目名が空ならエラーメッセージが返る。"""
        name, error = validate_and_build_name("salesforce", "")
        assert name is None
        assert "項目名" in error

    def test_invalid_characters_return_error(self):
        """使えない文字（日本語・スペース等）はエラーメッセージが返る。"""
        name, error = validate_and_build_name("セールスフォース", "password")
        assert name is None
        assert "半角英数字" in error


class TestSplitName:
    """split_name（キー名の分解）のテスト。"""

    def test_splits_simple_name(self):
        assert split_name("salesforce_password") == ("salesforce", "password")

    def test_splits_at_last_underscore(self):
        """アンダースコアが複数ある場合は最後で分ける。"""
        assert split_name("oju_sys_password") == ("oju_sys", "password")

    def test_name_without_underscore(self):
        """アンダースコアがない場合は全体をシステム名として扱う。"""
        assert split_name("token") == ("token", "")


class TestGuiSmoke:
    """画面が組み立てられることのスモークテスト（表示はしない）。"""

    def test_app_builds_and_destroys(self):
        """ウィンドウの生成～破棄までエラーが出ないことを確認する。"""
        import tkinter as tk

        from comken.credentials.gui import CredentialsApp

        try:
            root = tk.Tk()
        except tk.TclError:
            pytest.skip("ディスプレイのない環境では GUI を起動できない")

        root.withdraw()  # 画面には表示しない
        try:
            app = CredentialsApp(root)
            # 一覧の更新が例外なく動くこと
            app._refresh()
        finally:
            root.destroy()
