"""
Config クラスのテスト。

実行方法:
    リポジトリのルートで python -m pytest tests/ -v
"""

import pytest

from comken.config import Config
from comken.exceptions import ConfigError


class TestConfigMissingFile:
    def test_missing_file_raises_config_error(self, tmp_path):
        """config.ini が存在しない場合は ConfigError で即エラーになることを確認する。

        （configparser は黙って空になるため、後の分かりにくい AttributeError を防ぐ）
        """
        with pytest.raises(ConfigError, match="config.ini が見つかりません"):
            Config(tmp_path / "config.ini")


class TestConfigBasic:
    """Config の基本的な読み込みのテスト。"""

    def test_reads_string_value(self, tmp_path):
        """文字列の設定値を正しく読み込めることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[section]\nkey = hello\n", encoding="utf-8")
        config = Config(ini)
        assert config.SECTION.KEY == "hello"

    def test_section_and_key_are_uppercased(self, tmp_path):
        """セクション名・キー名が大文字に変換されることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[my_section]\nmy_key = value\n", encoding="utf-8")
        config = Config(ini)
        assert config.MY_SECTION.MY_KEY == "value"

    def test_multiple_sections(self, tmp_path):
        """複数セクションをそれぞれ読み込めることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text(
            "[salesforce]\nusername = user@example.com\n\n[report]\nfolder = output\n",
            encoding="utf-8",
        )
        config = Config(ini)
        assert config.SALESFORCE.USERNAME == "user@example.com"
        assert config.REPORT.FOLDER == "output"

    def test_default_path_is_config_ini(self, tmp_path, monkeypatch):
        """パス省略時にカレントディレクトリの config.ini を読むことを確認する。"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "config.ini").write_text("[s]\nk = v\n", encoding="utf-8")
        config = Config()
        assert config.S.K == "v"


class TestConfigBoolConversion:
    """bool 変換のテスト。"""

    def test_true_string_becomes_true(self, tmp_path):
        """'true' が bool の True に変換されることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nflag = true\n", encoding="utf-8")
        assert Config(ini).S.FLAG is True

    def test_false_string_becomes_false(self, tmp_path):
        """'false' が bool の False に変換されることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nflag = false\n", encoding="utf-8")
        assert Config(ini).S.FLAG is False

    def test_uppercase_true_becomes_true(self, tmp_path):
        """'True' / 'TRUE' など大文字混じりも変換されることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nflag = True\n", encoding="utf-8")
        assert Config(ini).S.FLAG is True

    @pytest.mark.parametrize("value", ["yes", "no", "on", "off", "1", "0"])
    def test_boolean_like_values_stay_string(self, tmp_path, value):
        """true / false 以外（yes / no / on / off / 1 / 0）は変換せず文字列のままを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text(f"[s]\nflag = {value}\n", encoding="utf-8")
        assert Config(ini).S.FLAG == value

    def test_number_stays_string(self, tmp_path):
        """数値は文字列のまま返すことを確認する（呼び出し側で変換する）。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\ncount = 10\n", encoding="utf-8")
        assert Config(ini).S.COUNT == "10"


class TestConfigParseList:
    """parse_list のテスト。"""

    def test_comma_separated(self, tmp_path):
        """カンマ区切りの文字列をリストに変換することを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nitems = a, b, c\n", encoding="utf-8")
        config = Config(ini)
        assert config.parse_list(config.S.ITEMS) == ["a", "b", "c"]

    def test_empty_values_excluded(self, tmp_path):
        """空文字列はリストから除外されることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nitems = a, , b\n", encoding="utf-8")
        config = Config(ini)
        assert config.parse_list(config.S.ITEMS) == ["a", "b"]
