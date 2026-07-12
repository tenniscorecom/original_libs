"""
Config クラスのテスト。

実行方法:
    リポジトリのルートで python -m pytest tests/ -v
"""

from pathlib import Path

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

    def test_reads_bom_utf8(self, tmp_path):
        """BOM 付き UTF-8 の config.ini も読めることを確認する。

        （メモ帳や PowerShell で保存すると BOM 付きになるため。
        BOM を素通しすると1つ目のセクションが MissingSectionHeaderError になる）
        """
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nk = 日本語\n", encoding="utf-8-sig")
        assert Config(ini).S.K == "日本語"


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

    @pytest.mark.parametrize("value", ["yes", "no", "on", "off"])
    def test_boolean_like_values_stay_string(self, tmp_path, value):
        """true / false 以外の yes / no / on / off は変換せず文字列のままを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text(f"[s]\nflag = {value}\n", encoding="utf-8")
        assert Config(ini).S.FLAG == value


class TestConfigTypeConversion:
    """int / float / Path 自動変換のテスト。"""

    def test_integer_value_becomes_int(self, tmp_path):
        """整数値が int に変換されることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\ncount = 10\n", encoding="utf-8")
        assert Config(ini).S.COUNT == 10
        assert isinstance(Config(ini).S.COUNT, int)

    def test_float_value_becomes_float(self, tmp_path):
        """小数値が float に変換されることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nratio = 1.5\n", encoding="utf-8")
        assert Config(ini).S.RATIO == 1.5
        assert isinstance(Config(ini).S.RATIO, float)

    def test_windows_absolute_path_becomes_path(self, tmp_path):
        """Windows 絶対パス（C:\\）が Path に変換されることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nfolder = C:\\work\\input\n", encoding="utf-8")
        from pathlib import Path
        assert Config(ini).S.FOLDER == Path("C:\\work\\input")

    def test_unc_path_becomes_path(self, tmp_path):
        """UNC パス（\\\\server\\...）が Path に変換されることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nfolder = \\\\nas\\reports\n", encoding="utf-8")
        from pathlib import Path
        assert isinstance(Config(ini).S.FOLDER, Path)

    def test_plain_string_stays_string(self, tmp_path):
        """数値・パスでない文字列はそのまま str で返ることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nname = T_data\n", encoding="utf-8")
        assert Config(ini).S.NAME == "T_data"
        assert isinstance(Config(ini).S.NAME, str)


class TestConfigListConversion:
    """LIST(...) 記法の自動変換のテスト。"""

    def test_comma_separated(self, tmp_path):
        """LIST(a, b, c) が自動でリストに変換されることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nitems = LIST(a, b, c)\n", encoding="utf-8")
        assert Config(ini).S.ITEMS == ["a", "b", "c"]

    def test_japanese_values(self, tmp_path):
        """日本語の値も変換されることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nsheets = LIST(東日本, 西日本, 集計)\n", encoding="utf-8")
        assert Config(ini).S.SHEETS == ["東日本", "西日本", "集計"]

    def test_empty_values_excluded(self, tmp_path):
        """空文字列はリストから除外されることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nitems = LIST(a, , b)\n", encoding="utf-8")
        assert Config(ini).S.ITEMS == ["a", "b"]

    def test_newline_separated(self, tmp_path):
        """改行区切りの複数行 LIST も変換されることを確認する。

        config.ini で複数行値を書く場合は、2行目以降を字下げ（スペースまたはタブ）する。

        [REPORT]
        TARGET_SHEETS = LIST(東日本
            西日本
            集計)
        """
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nitems = LIST(a\n\tb\n\tc)\n", encoding="utf-8")
        assert Config(ini).S.ITEMS == ["a", "b", "c"]

    def test_empty_list(self, tmp_path):
        """LIST() は空リストになることを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nitems = LIST()\n", encoding="utf-8")
        assert Config(ini).S.ITEMS == []

    def test_lowercase_list_stays_string(self, tmp_path):
        """小文字の list(...) は変換されず文字列のままを確認する（誤変換防止）。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nitems = list(a, b)\n", encoding="utf-8")
        assert Config(ini).S.ITEMS == "list(a, b)"

    def test_parse_list_still_works_with_warning(self, tmp_path):
        """旧方式の parse_list は FutureWarning 付きで動くことを確認する。"""
        ini = tmp_path / "config.ini"
        ini.write_text("[s]\nitems = a, b, c\n", encoding="utf-8")
        config = Config(ini)

        with pytest.warns(FutureWarning, match="LIST"):
            assert config.parse_list(config.S.ITEMS) == ["a", "b", "c"]


class TestGenerateStub:
    """generate_stub（エディタ補完用スタブ生成）のテスト。"""

    @pytest.fixture
    def ini(self, tmp_path):
        path = tmp_path / "config.ini"
        path.write_text(
            "[browser]\nwait_seconds = 10\nheadless = false\n"
            "[files]\ninput_folder = C:\\work\\input\nratio = 1.5\n"
            "[report]\nsheets = LIST(a, b)\nname = T_data\n",
            encoding="utf-8",
        )
        return path

    def test_generates_typed_sections(self, ini, tmp_path):
        """セクションごとのクラスと型注釈が生成されることを確認する。"""
        from comken.config import generate_stub

        out = generate_stub(ini, tmp_path / "config.pyi")
        text = out.read_text(encoding="utf-8")

        assert "class _BROWSER:" in text
        assert "    WAIT_SECONDS: int" in text
        assert "    HEADLESS: bool" in text
        assert "    INPUT_FOLDER: Path" in text
        assert "    RATIO: float" in text
        assert "    SHEETS: list[str]" in text
        assert "    NAME: str" in text

    def test_config_class_references_sections(self, ini, tmp_path):
        """Config クラスが各セクションクラスを属性に持つことを確認する。"""
        from comken.config import generate_stub

        text = generate_stub(ini, tmp_path / "config.pyi").read_text(encoding="utf-8")

        assert "class Config:" in text
        assert "    BROWSER: _BROWSER" in text
        assert "config: Config" in text

    def test_default_output_is_src_config_pyi(self, ini, tmp_path, monkeypatch):
        """src/config.py があるプロジェクトでは src/config.pyi に出力されることを確認する。"""
        from comken.config import generate_stub

        monkeypatch.chdir(tmp_path)
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "config.py").write_text(
            "from comken.config import Config\nconfig = Config()\n", encoding="utf-8"
        )

        out = generate_stub(ini)

        assert out == Path("src/config.pyi")
        assert (tmp_path / "src" / "config.pyi").exists()

    def test_missing_ini_raises(self, tmp_path):
        """config.ini がない場合は ConfigError になることを確認する。"""
        from comken.config import generate_stub

        with pytest.raises(ConfigError):
            generate_stub(tmp_path / "config.ini", tmp_path / "config.pyi")

    def test_stub_is_valid_python(self, ini, tmp_path):
        """生成されたスタブが Python として構文エラーにならないことを確認する。"""
        import ast

        from comken.config import generate_stub

        text = generate_stub(ini, tmp_path / "config.pyi").read_text(encoding="utf-8")
        ast.parse(text)  # 構文エラーなら例外になる
