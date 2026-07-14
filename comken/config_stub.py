"""
config_stub.py — config.ini からエディタ補完用スタブ（.pyi）を生成する

Config の属性（config.SECTION.KEY）は config.ini から実行時に動的に作られるため、
そのままではエディタが補完できない。ここで config.ini の内容を型付きの .pyi に書き出し、
補完を効かせる。設定値の読み込み（config.py）とは責務を分けている。

- Config() を呼ぶたびに update_stub() が自動で走る（config.py から呼ばれる）
- コードを書く前に手動で作りたい場合は generate_stub()（`python -m comken.config`）
"""

import configparser
import os
from pathlib import Path

from .config import _parse_value
from .exceptions import ConfigError
from .utils.file import cleanup_stale_tmp as _cleanup_stale_tmp

_STUB_HEADER = '''"""config.ini から自動生成されたエディタ補完用スタブ。手で編集しない。

Config() を呼ぶたびに自動更新される（手動生成: python -m comken.config）。
"""
'''


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
            raise ConfigError(
                ConfigError.MSG_STUB_TARGET.format(path=Path(ini_path).resolve().parent)
            )
    output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_build_stub_content(cfg), encoding="utf-8")
    return output_path


def update_stub(cfg: configparser.ConfigParser, ini_path: str | Path) -> None:
    """スタブを自動更新する（Config() から呼ばれる。失敗しても本処理は止めない）。

    - src/config.py がないプロジェクトでは何もしない
    - 内容が変わっていなければ書き込まない（無駄なファイル更新をしない）
    """
    stub_path = _resolve_stub_path(ini_path)
    if stub_path is None:
        return
    _cleanup_stale_tmp(stub_path)  # 前回クラッシュ時の .tmp 残骸を掃除
    content = _build_stub_content(cfg)
    try:
        if stub_path.exists() and stub_path.read_text(encoding="utf-8") == content:
            return
        # 一時ファイル経由で置き換える（複数プロセス同時起動時の書き込み競合対策）
        tmp_path = stub_path.with_suffix(f"{stub_path.suffix}.{os.getpid()}.tmp")
        tmp_path.write_text(content, encoding="utf-8")
        os.replace(tmp_path, stub_path)
    except OSError:
        pass  # 読み取り専用フォルダ等。補完が更新されないだけで実行には影響しない


# ── 内部ヘルパー ──────────────────────────────────────────────────────────────


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
