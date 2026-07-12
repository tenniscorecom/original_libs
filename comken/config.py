"""
config.py — INI ファイル読み込みユーティリティ

config.ini を読み込み、config.SECTION.KEY の形式でアクセスできる Config クラスを提供する。

プロジェクト側での使い方:
    src/config.py でシングルトンを作り、各モジュールからインポートする。

        # src/config.py
        from comken.config import Config
        config = Config()

        # 各モジュール
        from .config import config
        path = config.FILES.CSV_INPUT_FOLDER / config.FILES.CSV_EAST

エディタの補完候補:
    属性は実行時に動的に作られるため、そのままではエディタが補完できないが、
    Config() を呼ぶたびに補完用のスタブ（src/config.pyi）が自動更新されるため、
    一度スクリプトを実行すれば config.SECTION.KEY が型付きで補完されるようになる。

    まだ一度も実行していない状態で先にスタブだけ作りたい場合は手動で生成する:

        python -m comken.config

※ ブラウザの設定は config.ini ではなく BrowserOptions のインスタンス
   （src/browser_options.py）で行う。config はブラウザ設定を持たない。
"""

import configparser
import os
import types
import warnings
from pathlib import Path

from .exceptions import ConfigError


def _split_list_items(text: str) -> list[str]:
    """カンマまたは改行区切りの文字列をリストに変換する。空文字は除外する。"""
    items = text.replace("\n", ",").split(",")
    return [s.strip() for s in items if s.strip()]


def _parse_value(
    cfg: configparser.ConfigParser, section: str, key: str
) -> bool | int | float | Path | list[str] | str:
    """ini の値を適切な Python 型に変換して返す。

    変換の優先順位:
        1. true / false（大文字小文字問わず）→ bool
        2. [a, b, c] → list[str]（改行区切りも可）
        3. 絶対パス（C:\\ / \\\\ / / で始まる）→ Path
        4. 整数に変換できる → int
        5. 小数に変換できる → float
        6. それ以外 → str

    文字列として使いたい数値（例: シート名 "2024"）はコード側で str() に変換する。
    """
    value = cfg.get(section, key).strip()
    lower = value.lower()

    if lower == "true":
        return True
    if lower == "false":
        return False

    if value.startswith("[") and value.endswith("]"):
        return _split_list_items(value[1:-1])

    if len(value) >= 2 and (value[1:3] == ":\\" or value[:2] == "\\\\" or value[0] == "/"):
        return Path(value)

    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass

    return value


class Config:
    """config.ini を読み込み、config.SECTION.KEY の形式でアクセスできるクラス。

    値の型変換（_parse_value の変換順と同じ）:
        - true / false → bool
        - [a, b, c] → list[str]
        - 絶対パス（C:\\ / \\\\ / /）→ Path
        - 整数 → int
        - 小数 → float
        - それ以外 → str

    数値を文字列として使いたい場合はコード側で str() に変換する。

    config.ini の例（セクション名・キー名は大文字で書く）:
        [BROWSER]
        WAIT_SECONDS = 10
        HEADLESS = false

        [FILES]
        INPUT_FOLDER = C:\\作業\\input

        [REPORT]
        TARGET_SHEETS = [東日本, 西日本, 集計]

    使い方:
        config = Config() # カレントディレクトリの config.ini を読む
        config = Config("path/to/config.ini") # パスを指定する場合

        config.BROWSER.HEADLESS        # → False（bool）
        config.BROWSER.WAIT_SECONDS    # → 10（int）
        config.FILES.INPUT_FOLDER      # → Path("C:\\作業\\input")
        config.FILES.INPUT_FOLDER / "東日本.csv"  # → Path("C:\\作業\\input\\東日本.csv")
        config.REPORT.TARGET_SHEETS    # → ["東日本", "西日本", "集計"]
    """

    def __init__(self, path: str | Path = "config.ini") -> None:
        """
        Args:
            path: config.ini のパス。省略するとカレントディレクトリの config.ini を読む。
        """
        cfg = configparser.ConfigParser()
        # utf-8-sig: メモ帳等で保存すると BOM 付き UTF-8 になるため（BOM なしも読める）
        loaded = cfg.read(path, encoding="utf-8-sig")
        if not loaded:
            # configparser はファイルがなくても黙って空になるため、明示的にエラーにする
            # （後で config.FILES 等が分かりにくい AttributeError になるのを防ぐ）
            raise ConfigError(ConfigError.MSG.format(path=Path(path).resolve()))

        for section in cfg.sections():
            ns = types.SimpleNamespace(
                **{k.upper(): _parse_value(cfg, section, k) for k in cfg.options(section)}
            )
            setattr(self, section.upper(), ns)

        # エディタ補完用スタブ（src/config.pyi）を自動更新する。
        # config.ini を変更してもスタブが古くならない（失敗しても本処理は止めない）
        _update_stub(cfg, path)

    def parse_list(self, value: str) -> list[str]:
        """【旧方式】カンマまたは改行区切りの文字列をリストに変換する。

        現在は config.ini 側で [a, b, c] と書けば自動でリストに変換されるため、
        このメソッドを呼ぶ必要はない。旧コードを壊さないために残している。

        Args:
            value: カンマまたは改行区切りの文字列。

        Returns:
            空文字を除いた文字列のリスト。
        """
        warnings.warn(
            "parse_list は不要になりました。config.ini 側で [a, b, c] と書くと"
            "自動でリストに変換されます（改行区切りも可）。",
            FutureWarning,
            stacklevel=2,
        )
        return _split_list_items(value)


# ── エディタ補完用スタブの生成 ─────────────────────────────────────────────────

_STUB_HEADER = '''"""config.ini から自動生成されたエディタ補完用スタブ。手で編集しない。

Config() を呼ぶたびに自動更新される（手動生成: python -m comken.config）。
"""
'''


def _stub_type_name(value: bool | int | float | Path | list | str) -> str:
    """スタブに書く型名を返す。"""
    if isinstance(value, bool):  # bool は int のサブクラスなので先に判定する
        return "bool"
    if isinstance(value, Path):
        return "Path"
    if isinstance(value, list):
        return "list[str]"
    return type(value).__name__


def _build_stub_content(cfg: configparser.ConfigParser) -> str:
    """読み込み済みの ConfigParser からスタブファイルの中身を組み立てる。"""
    section_lines: list[str] = []
    config_attrs: list[str] = []
    for section in cfg.sections():
        class_name = f"_{section.upper()}"
        config_attrs.append(f"    {section.upper()}: {class_name}")
        section_lines.append(f"class {class_name}:")
        options = cfg.options(section)
        if not options:
            section_lines.append("    pass")
        for key in options:
            value = _parse_value(cfg, section, key)
            section_lines.append(f"    {key.upper()}: {_stub_type_name(value)}")
        section_lines.append("")

    # Path は Config.__init__ のシグネチャでも使うため常に import する
    lines = [_STUB_HEADER, "from pathlib import Path\n", ""]
    lines.extend(section_lines)
    lines.append("class Config:")
    lines.extend(config_attrs or ["    pass"])
    lines.append("    def __init__(self, path: str | Path = ...) -> None: ...")
    lines.append("    def parse_list(self, value: str) -> list[str]: ...")
    lines.append("")
    lines.append("config: Config")
    return "\n".join(lines) + "\n"


def _resolve_stub_path(ini_path: str | Path) -> Path | None:
    """スタブの出力先を config.ini の場所を基準に決める。

    .pyi は同名の .py の隣に置かないとエディタに認識されないため、
    src/config.py（推奨構成）→ config.py の順に探し、どちらもなければ None。
    """
    base = Path(ini_path).resolve().parent
    if (base / "src" / "config.py").exists():
        return base / "src" / "config.pyi"
    if (base / "config.py").exists():
        return base / "config.pyi"
    return None


def _update_stub(cfg: configparser.ConfigParser, ini_path: str | Path) -> None:
    """スタブを自動更新する（Config() から呼ばれる。失敗しても本処理は止めない）。

    - src/config.py がないプロジェクトでは何もしない
    - 内容が変わっていなければ書き込まない（無駄なファイル更新をしない）
    """
    stub_path = _resolve_stub_path(ini_path)
    if stub_path is None:
        return
    content = _build_stub_content(cfg)
    try:
        if stub_path.exists() and stub_path.read_text(encoding="utf-8") == content:
            return
        # 一時ファイル経由で置き換える（複数プロセス同時起動時の書き込み競合対策）
        tmp_path = stub_path.with_suffix(f".pyi.{os.getpid()}.tmp")
        tmp_path.write_text(content, encoding="utf-8")
        os.replace(tmp_path, stub_path)
    except OSError:
        pass  # 読み取り専用フォルダ等。補完が更新されないだけで実行には影響しない


def generate_stub(
    ini_path: str | Path = "config.ini", output_path: str | Path | None = None
) -> Path:
    """config.ini からエディタ補完用の型スタブ（.pyi）を手動生成する。

    通常は Config() を呼ぶたびに自動更新されるため、手動で実行する必要はない。
    「コードをまだ書いていないが先にスタブだけ作りたい」場合に使う:

        python -m comken.config

    Args:
        ini_path: 読み込む config.ini のパス。
        output_path: スタブの出力先。省略時は config.ini と同じ場所を基準に
                     src/config.pyi → config.pyi の順に決める。

    Returns:
        生成したスタブファイルのパス。

    Raises:
        ConfigError: config.ini が見つからない場合、または出力先を決められない場合
                     （src/config.py も config.py も存在しない）。
    """
    cfg = configparser.ConfigParser()
    loaded = cfg.read(ini_path, encoding="utf-8-sig")
    if not loaded:
        raise ConfigError(ConfigError.MSG.format(path=Path(ini_path).resolve()))

    if output_path is None:
        output_path = _resolve_stub_path(ini_path)
        if output_path is None:
            raise ConfigError(ConfigError.MSG_STUB_TARGET.format(path=Path(ini_path).resolve().parent))
    output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_build_stub_content(cfg), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    stub_path = generate_stub()
    print(f"補完用スタブを生成しました: {stub_path.resolve()}")
    print("以後は Config() を呼ぶたびに自動更新されます。")
