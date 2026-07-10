# コーディング規約

comken ライブラリおよびこのライブラリを使うプロジェクトで共通して使うルール。
**PEP 8**（Python 公式スタイルガイド）に準拠し、矛盾する場合は本規約を優先する。

---

## 目次

1. [基本方針](#基本方針)
2. [命名規則](#命名規則)
3. [パッケージ・ファイル構成](#パッケージファイル構成)
4. [公開 API の管理](#公開-api-の管理)
5. [型ヒント](#型ヒント)
6. [定数とマジックナンバー](#定数とマジックナンバー)
7. [設定の上書きパターン](#設定の上書きパターン)
8. [リソース管理（with 文）](#リソース管理with-文)
9. [例外](#例外)
10. [ロギング](#ロギング)
11. [Excel（openpyxl）](#excelopenpyxl)
12. [Windows 操作（pywin32）](#windows-操作pywin32)
13. [コメント](#コメント)
14. [Page Object Model](#page-object-model)
15. [循環インポートの解決](#循環インポートの解決)
16. [テスト](#テスト)
17. [プロジェクトセットアップファイル](#プロジェクトセットアップファイル)
18. [開発環境（VS Code）](#開発環境vs-code)

---

## 基本方針

- **Ruff** に準拠する（PEP 8）
- **型ヒント**を必ず書く
- **マジックナンバー禁止**。数値・文字列定数は名前付き定数にする
- `print` は禁止。ログは `logging` を使う
- コメントは「なぜ」を書く。コードを読めば分かる「何を」は書かない

---

## 命名規則

Python の作法（PEP 8）に従う。

| 種別 | 規則 | 例 |
|---|---|---|
| クラス名 | PascalCase | `ExcelFile`, `LoginPage`, `CsvMerger` |
| 定数・固定値 | UPPER_SNAKE_CASE | `COL_Q`, `SHEET_NAME`, `WAIT_SECONDS` |
| 関数・メソッド | snake_case | `read_rows()`, `find_today_file()` |
| 変数 | snake_case | `csv_lookup`, `matched_rows` |
| モジュール・ファイル名 | snake_case | `handler.py`, `base_page.py` |
| フォルダ名 | snake_case | `excel/`, `browser/` |
| 内部用（外から呼ばない） | `_` プレフィックス | `_sheet()`, `_click()` |
| config.ini のセクション・キー | UPPER_SNAKE_CASE | `[CREDENTIALS]`, `OUTPUT_FOLDER` |
| テストクラス | `Test` + PascalCase | `TestExcelFile`, `TestCsvReader` |
| テストメソッド | `test_` + snake_case | `test_reads_all_rows` |

### 名前の付け方の原則

| ルール | 良い例 | 悪い例 |
|---|---|---|
| 役割が分かる名前にする | `find_today_file` | `get_file`, `f` |
| 略しすぎない | `sheet_name` | `sn`, `s` |
| bool は is / has / can で始める | `is_empty`, `has_header` | `empty`, `header` |
| 返り値が複数なら複数形 | `rows`, `records` | `row`, `record` |
| 否定形の変数名を使わない | `is_valid = True` | `is_invalid = False` |

### 定数を大文字にする理由

**大文字にすることで「これは変更しない値だ」とコードを読む人が一目で判断できる。**
設定ファイルから読み込んだ値も定数として扱い、大文字で定義する。

```python
# 悪い（変数と区別がつかない）
col_q = 17
sheet_name = "T_data"

# 良い（定数と分かる）
COL_Q = 17
SHEET_NAME = "T_data"
```

config.ini のセクション名・キー名も同じ理由で大文字にする。
Python 側のアクセス（`config.BROWSER.HEADLESS`）と表記が完全に一致するので対応が追いやすい。

---

## パッケージ・ファイル構成

### プロジェクトの構造

```
my_project/
  main.py ← エントリポイント（python main.py で実行）
  config.ini ← 非機密の設定（.gitignore に追加）
  config.ini.example ← 設定のテンプレート（git に含める）
  ERRORS.md ← エラー対応ガイド（非エンジニア向け）
  src/
    config.py ← AppConfig（comken.Config を継承）
    browser_options.py ← MyOptions（comken.BrowserOptions を継承）
    pages/ ← 画面クラス（SitePage を継承）
    excel/ ← Excel 処理
    salesforce/ ← Salesforce 連携
```

| ファイル | 場所 | 役割 |
|---|---|---|
| `main.py` | ルート | `python main.py` で直接実行できる |
| `config.ini` | ルート | URL・フォルダパス・フラグ等の**非機密設定**のみ |
| `config.ini.example` | ルート | 設定テンプレート。git に含めてチームで共有する |
| `ERRORS.md` | ルート | エラー名から対処を引ける表。comken の雛形をコピーし、プロジェクト固有のエラーを追記する |
| `src/` 以下 | `src/` | コードだけ。エンジニアの管理領域 |

> **パスワード・トークンだけでなく、ユーザー名・メールアドレスなど個人情報になりそうなものはすべて config.ini に書かない。**
> 認証情報は各ユーザーが `python -m comken.credentials` で1回だけ登録し、コードからは `comken.credentials.load_credential()` で取得する（Windows DPAPI でログオンユーザーに紐付けて暗号化されるため、ユーザーごとに自動で分かれる）。

**暗号化ファイルはプロジェクト内には置かない。**
保存先は `%USERPROFILE%\.comken\credentials.dat`（ユーザープロファイル内）で固定。

| プロジェクト外に置く理由 | 詳細 |
|---|---|
| git に混入しない | プロジェクトフォルダに置くと commit 事故のリスクがある |
| 全プロジェクトで共有できる | 一度登録すれば別のプロジェクトからも同じ認証情報を使える |
| ユーザーごとに自動で分かれる | ユーザープロファイル内なので他人のファイルと混ざらない |

> **`src/main.py` にしない理由:** `src/main.py` にすると `Config("../config.ini")` と上の階層を参照する必要が生じる。コードは下の階層（`src/`）だけを参照するのが自然。

---

## 公開 API の管理

### `__all__` で公開範囲を明示する

```python
# comken/excel/__init__.py
from .handler import ExcelFile

__all__ = ["ExcelFile"]
```

`__all__` を書くと内部の実装クラスが外に漏れ出さない。

### 内部ヘルパーには `_` プレフィックスを付ける

```python
class ExcelFile:
    def read_rows(self, sheet_name: str) -> list[tuple]:  # 公開メソッド
        ws = self._sheet(sheet_name)
        ...

    def _sheet(self, sheet_name: str):  # 外から直接呼ばないという意味
        ...
```

---

## 型ヒント

すべての関数に引数・戻り値の型ヒントを付ける。

```python
# 悪い（型が分からない）
def find_today_file(folder, pattern="*.xlsx"):
    ...

# 良い
def find_today_file(folder: str | Path, pattern: str = "*.xlsx") -> Path | None:
    ...
```

| よく使う型ヒント | 意味 |
|---|---|
| `str \| None` | 文字列または None |
| `Path \| str` | Path オブジェクトまたは文字列 |
| `list[dict]` | 辞書のリスト |
| `dict[str, list]` | キーが文字列、値がリストの辞書 |
| `X \| None` | `Optional[X]` の代わりに使う（Python 3.10+） |

- `Any` は使わない（型チェックが無意味になる）

---

## 定数とマジックナンバー

コードの中に突然出てくる意味不明な数値や文字列を**マジックナンバー**と呼ぶ。

```python
# 悪い例（マジックナンバー）
rows = f.read_rows("売上データ", min_row=2)
if file_size > 10485760:
    ...
```

```python
# 良い例（名前付き定数）
SHEET_NAME = "売上データ"
HEADER_ROW = 1
LOCAL_COPY_THRESHOLD_MB = 10
LOCAL_COPY_THRESHOLD_BYTES = LOCAL_COPY_THRESHOLD_MB * 1024 * 1024  # 計算式のまま書く

rows = f.read_rows(SHEET_NAME, min_row=HEADER_ROW + 1)
if file_size > LOCAL_COPY_THRESHOLD_BYTES:
    ...
```

| ルール | 詳細 |
|---|---|
| **大文字スネークケース** | `SHEET_NAME`, `MAX_RETRY_COUNT` |
| **場所** | ファイルの先頭またはクラスの先頭（メソッドより上）にまとめる |
| **計算式はそのまま書く** | `10 * 1024 * 1024`（`10485760` より意味が伝わる） |

---

## 設定の上書きパターン

comken のクラスはデフォルト値を持っており、プロジェクト側でサブクラスを作って上書きする。
変更したい項目だけ書けばよく、他はデフォルト値が使われる。

```python
# src/browser_options.py
from comken.browser.options import BrowserOptions

class MyOptions(BrowserOptions):
    HEADLESS = True
    DOWNLOAD_DIR = r"\\nas-server\reports"
    WAIT_SECONDS = 20
```

**config.ini に書くのは非機密のプロジェクト固有の値だけ。**
URL・フォルダパス・フラグなど、環境によって変わるが秘匿不要なものを書く。
**個人情報・パスワード・トークン・メールアドレス等はすべて `comken.credentials` で暗号化して保存する。**

```ini
; config.ini（非機密の値のみ。セクション名・キー名は大文字で書く）
[CREDENTIALS]
; ユーザー名・パスワード・トークンは python -m comken.credentials で登録する
; どのサービス名で登録した認証情報を使うかだけをここに書く（キー名は機密ではない）
SALESFORCE = salesforce

[BROWSER]
HEADLESS = False

[REPORT]
OUTPUT_FOLDER = \\nas-server\reports
```

```python
# config.py での読み込みパターン（読んだ値は大文字で定数として定義する）
import configparser

_cfg = configparser.ConfigParser()
_cfg.read("config.ini", encoding="utf-8")

HEADLESS: bool = _cfg.getboolean("BROWSER", "HEADLESS")
OUTPUT_DIR: str = _cfg.get("REPORT", "OUTPUT_FOLDER")
SF_PREFIX: str = _cfg.get("CREDENTIALS", "SALESFORCE")
```

認証情報は config.ini ではなく `comken.credentials` から取得する。
キー名の直書き（マジックナンバー化）を避けるため、`Credentials` にプレフィックスを渡して属性で取り出す。

```python
from comken.credentials import Credentials

# 事前に python -m comken.credentials で登録しておく
cred = Credentials(SF_PREFIX)  # プレフィックスは config.ini から
sf = SalesforceClient(
    username=cred.username,     # → salesforce_username の値
    password=cred.password,     # → salesforce_password の値
    security_token=cred.token,  # → salesforce_token の値
)
```

### キー名の付け方

キー名1つに値1つを何件でも登録できる（上書きになるのは同じキー名のときだけ）。
「ユーザー名とパスワードが必ずセット」という決め打ちはしないので、パスワードだけのシステムにも対応できる。

```
credentials.dat（1ユーザーにつき1ファイル、中身はキーと値のペア）
{
  "salesforce_username": "user@example.com",
  "salesforce_password": "xxxx",
  "salesforce_token": "yyyy",
  "oju_sys_password": "zzzz"
}
```

| ルール | 例 |
|---|---|
| `システム名_項目名` の形式にする | `salesforce_password`, `oju_sys_password` |
| アカウントを使い分けるときはシステム名に用途を含める | `salesforce_test_password` |

> **キー名に使えるのは半角英数字とアンダースコアのみ。**
> それ以外（漢字・スペース・記号）はライブラリ側で弾かれる（`InvalidCredentialNameError`）。

**どのシステム名（プレフィックス）を使うかは config.ini の `[CREDENTIALS]` セクションに書く。**
`SALESFORCE = salesforce_test` に変えるだけで、`Credentials` 経由の username / password / token が
すべてテスト用に切り替わる。コードは1文字も触らない。

### 使う認証情報はコード側で宣言する

プロジェクトが使う認証情報は `src/config.py` に `REQUIRED_CREDENTIALS` として宣言する。
登録ツール（`python -m comken.credentials`）がこの宣言を読み取り、
未登録の項目だけを順に聞く「まとめて登録」が使えるようになる（キー名を手入力しないのでスペルミスが起きない）。

```python
# src/config.py
REQUIRED_CREDENTIALS = {
    "SALESFORCE": ["username", "password", "token"],  # キーは config.ini [CREDENTIALS] のキー名
    "OJU_SYS": ["password"],
}
```

| ルール | 理由 |
|---|---|
| 宣言は config.ini ではなくコード側に置く | 「コードが何を使うか」はコードの事実。設定ファイルに書くと二重管理になる |
| 辞書のキーは config.ini `[CREDENTIALS]` のキー名 | プレフィックス切り替え（本番⇔テスト）が宣言側に波及する |
| コードで使う項目を増やしたら宣言も更新する | 宣言が実態とズレると「まとめて登録」で項目が漏れる |

---

## リソース管理（with 文）

ファイル・ドライバー・COM オブジェクトは必ず `with` 文または `try/finally` で確実に解放する。

| 方法 | 挙動 |
|---|---|
| `with` 文 | ブロックを抜けると自動で `close()`（例外が起きても確実に閉じる） |
| 手動 `close()` | 途中で例外が起きると実行されない → ファイルが開きっぱなし |

```python
# 良い（with 文）
with ExcelFile("data.xlsx") as f:
    rows = f.read_rows_as_dicts("Sheet1")

# with が使えない場合（pywin32 の COM オブジェクト等）
excel = None
try:
    excel = win32com.client.Dispatch("Excel.Application")
    # 処理
finally:
    if excel:
        excel.Quit()
```

Excel ファイルが開きっぱなしになると、次に開こうとしたときに「ファイルが使用中」エラーになる。

---

## 例外

### comken が定義するカスタム例外

| 例外クラス | 意味 | 発生するタイミング |
|---|---|---|
| `OriginalLibsError` | ライブラリ全体の基底例外 | — |
| `ExcelError` | Excel 系エラーの基底 | — |
| `SheetNotFoundError` | 指定したシートが存在しない | `read_rows()` 等でシート名を間違えたとき |
| `MacroError` | VBA マクロの実行エラー | `run_macro()` でマクロが失敗したとき |
| `CsvError` | CSV 系エラー | CSV の読み書きに失敗したとき |
| `ColumnNotFoundError` | 指定した列が存在しない | 列名を間違えたとき |
| `ConfigError` | 設定ファイルのエラー | config.ini が読めないとき |
| `CredentialError` | 認証情報エラーの基底 | — |
| `CredentialNotFoundError` | 認証情報が未登録 | `load_credential()` で未登録のキー名を指定したとき |
| `InvalidCredentialNameError` | キー名が不正 | 半角英数字・アンダースコア以外を含む名前で登録しようとしたとき |

### try / except での受け取り方

カスタム例外を定義している理由は**呼び出し側で「どのエラーか」を判別できるようにするため**。

```python
from comken.exceptions import SheetNotFoundError, ExcelError, OriginalLibsError

try:
    with ExcelFile("data.xlsx") as f:
        rows = f.read_rows("存在しないシート")

except SheetNotFoundError as e:
    logger.error("シートが見つかりません: %s", e)

except ExcelError as e:
    logger.error("Excel エラー: %s", e)

except OriginalLibsError as e:
    logger.error("ライブラリエラー: %s", e)
```

**粒度の使い分け:**

| except の粒度 | 使いどころ |
|---|---|
| `SheetNotFoundError` | そのエラーだけ個別に対応したいとき |
| `ExcelError` | Excel 系のエラーをまとめて処理したいとき |
| `OriginalLibsError` | comken のエラーを全部キャッチしたいとき |

- **例外は握りつぶさない**（`except: pass` は禁止）
- エラーメッセージには「何が・どこで・なぜ」を含める

---

## ロギング

`print` は禁止。必ず `logging` を使う。

```python
import logging

logger = logging.getLogger(__name__)

logger.info("処理開始: %s", file_path)
logger.debug("詳細: %s", value)
logger.warning("ファイルが見つかりません: %s", path)
logger.error("エラーが発生しました", exc_info=True)  # exc_info=True でスタックトレースも出力
```

**`print` を禁止にする理由:**

| | print | logging |
|---|---|---|
| ログレベル（INFO/ERROR 等） | なし | あり |
| ファイルへの出力 | できない | できる |
| 本番環境での抑制 | できない | できる |
| スタックトレースの出力 | 手動で書く | `exc_info=True` で自動 |

---

## Excel（openpyxl）

Excel の読み書きは comken の `ExcelFile` を使う。openpyxl を直接触るのは comken にない機能が必要なときだけ。

### 書式設定は処理ロジックと分離する

```python
from openpyxl.styles import Font, PatternFill, Alignment

def apply_header_style(cell) -> None:
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill(fill_type="solid", fgColor="4472C4")
    cell.alignment = Alignment(horizontal="center", vertical="center")
```

### 禁止事項

| 禁止 | 理由 |
|---|---|
| `data_only=False` のまま数式セルを上書き | 数式が消える |
| 巨大ファイルをそのまま `load_workbook` | メモリ不足。`read_only=True` を使う |

---

## Windows 操作（pywin32）

### 使用場面

pywin32 は **Windows 固有の API** に限定して使う。
ファイル操作は標準ライブラリの `shutil` / `pathlib` を優先する。

| 用途 | 推奨 |
|---|---|
| ファイルコピー・移動・削除 | `shutil`, `pathlib`（標準） |
| VBA マクロの実行 | `pywin32`（COM 経由） |
| ウィンドウ操作 | `pywin32`（win32gui） |
| レジストリ操作 | `pywin32`（win32api） |

COM オブジェクトは `with` 文が使えないため、`try/finally` で確実に解放する（[リソース管理（with 文）](#リソース管理with-文) 参照）。

### pywin32 の例外

```python
import pywintypes

try:
    pass  # win32 処理
except pywintypes.error as e:
    logger.error("Win32 API エラー: code=%d, msg=%s", e.winerror, e.strerror)
    raise
```

---

## コメント

### 通常コメント

「なぜ」を書く。コードを読めば分かる「何を」は書かない。

```python
# 良い例（なぜを説明している）
# NAS 上の大きなファイルを直接開くと遅く不安定なため、ローカルにコピーしてから開く
if src.stat().st_size > threshold:
    shutil.copy2(src, tmp_path)

# 悪い例（コードを読めば分かる）
i = i + 1  # i に 1 を加算する
rows = f.read_rows()  # 行を読み込む
```

### アノテーションコメント

IDE やエディタが認識する作業メモ用のタグ。`# タグ: 内容` の形式で書く。

| タグ | 意味 | 使いどころ |
|---|---|---|
| `TODO` | あとで追加・修正すべき | 未実装の機能、後回しにしたこと |
| `FIXME` | 既知の不具合がある | 動くが正しくない箇所 |
| `HACK` | きれいでない実装 | 暫定対応、リファクタリングが必要 |
| `XXX` | 危険・動く理由が不明 | 触ると壊れそうな箇所 |
| `REVIEW` | 動作確認が必要 | 意図通りか怪しい箇所 |
| `OPTIMIZE` | パフォーマンス改善が必要 | ボトルネックになっている箇所 |
| `NOTE` | なぜこうなったかの説明 | 仕様上の制約・背景情報 |
| `WARNING` | 注意が必要 | 副作用・前提条件がある箇所 |
| `CHANGED` | どう変更したかの記録 | 変更履歴をコードに残したいとき |

```python
# TODO: エラー時のリトライ処理を追加する
# FIXME: 列数が0のとき IndexError になる
# HACK: openpyxl のバグで数式が壊れるため、保存前に一時的に無効化する
# NOTE: この関数は NAS パスのみ対応。ローカルパスは local_copy() を使うこと
# WARNING: この処理はファイルを上書きする。バックアップを取ってから実行すること
```

### 特殊コメント（ツール向け）

ツールが解釈する「魔法のコメント」。コードの動作ではなくツールの挙動を制御する。

#### `# noqa` — リント警告を抑制する（Ruff / flake8）

```python
from module import something  # noqa: F401  # F401 = インポート未使用の警告を無視
x = 1+1  # noqa: E226  # E226 = スペースなし演算子の警告を無視
```

#### `# type: ignore` — 型チェックエラーを抑制する（mypy / pyright）

```python
result = some_func()  # type: ignore[return-value]  # 返り値の型が合わないが意図的
value = d.get("key")  # type: ignore[assignment]  # None になり得るが確認済み
```

#### `# fmt: off` / `# fmt: on` — フォーマッターを一時的に無効化する

```python
# fmt: off
matrix = [
    1, 0, 0,
    0, 1, 0,
    0, 0, 1,
]
# fmt: on
```

#### `# pragma: no cover` — カバレッジ計測から除外する（pytest-cov）

```python
if __name__ == "__main__":  # pragma: no cover
    main()
```

#### 使い方の原則

| ルール | 理由 |
|---|---|
| 必ず理由もコメントに書く | 「なぜ抑制しているか」が後で分からなくなる |
| `# noqa`（エラーコードなし）は乱用しない | 本物のバグも一緒に隠してしまう |
| できるだけ根本原因を修正する | 特殊コメントは最終手段 |

---

## Page Object Model

ブラウザ操作は必ず Page Object パターンで書く。
selenium を直接 import しない。要素の操作・待機はすべて `BasePage` のメソッド（`click_id`, `input_css`, `wait_visible_id` 等）を使う。

| ルール | 理由 |
|---|---|
| `time.sleep` は原則禁止（`wait_visible_*` 等を使う） | 固定待機は遅いうえに不安定 |
| セレクターは id > css > xpath の優先順で選ぶ | id が最も壊れにくい |
| xpath の絶対パス（`/html/body/div[2]/...`）は禁止 | 画面の構造が少し変わるだけで壊れる |

### 継承の構造

| クラス | 提供元 | 役割 |
|---|---|---|
| `BasePage` | comken | click / input / select / alert 等のブラウザ操作の道具箱 |
| `SitePage` | comken | `BASE_URL` と `go()` を追加 |
| `AppPage` | プロジェクトで作る | サイト共通処理（ヘッダー操作・共通エラー取得等） |
| `LoginPage` 等 | プロジェクトで作る | 各画面の操作 |

### AppPage（サイト共通ベースクラス）

```python
# src/pages/app_page.py
from comken.browser.site_page import SitePage

class AppPage(SitePage):
    BASE_URL = "https://example.com"

    def get_flash_message(self) -> str:
        return self.text_css("#flash")
```

### 各画面クラス

```python
# src/pages/login_page.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dashboard_page import DashboardPage

class LoginPage(AppPage):
    PATH = "/login"
    USERNAME_ID = "username"  # セレクターは定数（大文字）でクラス上部にまとめる
    LOGIN_BTN_CSS = ".radius"

    def open(self) -> None:
        self.go(self.PATH)

    def login(self, username: str, password: str) -> DashboardPage:
        """ログインして DashboardPage を返す。"""
        from .dashboard_page import DashboardPage  # 循環インポート対策

        self.input_id(self.USERNAME_ID, username)
        self.click_css(self.LOGIN_BTN_CSS)
        return DashboardPage(self._driver)
```

| ルール | 理由 |
|---|---|
| セレクターは定数（大文字）でクラス上部にまとめる | 変更箇所が1か所になる |
| 遷移メソッドは遷移先クラスを返す | 呼び出し側がコードの流れを追いやすくなる |

---

## 循環インポートの解決

2つの画面クラスが互いを参照するとき（`LoginPage` → `DashboardPage`、`DashboardPage` → `LoginPage`）に発生する。
`TYPE_CHECKING` + lazy import の組み合わせで解決する。

```python
from __future__ import annotations  # ① 型注釈を文字列として扱う（実行時評価しない）
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dashboard_page import DashboardPage  # ② IDE 補完用（ランタイムでは import されない）

class LoginPage(AppPage):
    def login(self, username: str, password: str) -> DashboardPage:  # ① のおかげで文字列扱い
        from .dashboard_page import DashboardPage  # ③ 実行時に必要なタイミングだけ import

        self.click_css(self.LOGIN_BTN_CSS)
        return DashboardPage(self._driver)
```

| 方法 | IDE補完 | 実行時 |
|---|---|---|
| `TYPE_CHECKING` のみ | ○ | エラー（`DashboardPage` が未定義） |
| lazy import のみ | × | ○ |
| **① + ② + ③ 全部** | **○** | **○** |

---

## テスト

テストは**参考パターン**として。書き方を知っておくと後で助かる。

### ファイル構成

```
tests/
  __init__.py
  test_config.py
  test_csv.py
  test_utils.py
```

### 書き方のパターン

```python
class TestCsvReaderFind:
    def test_finds_existing_row(self, sample_csv):
        """キーに一致する行を返す。"""
        row = CsvReader(sample_csv).find("注文番号", "A001")
        assert row is not None
        assert row["金額"] == "1000"

    def test_returns_none_when_not_found(self, sample_csv):
        """見つからない場合は None を返す。"""
        row = CsvReader(sample_csv).find("注文番号", "Z999")
        assert row is None
```

| ルール | 例 |
|---|---|
| テストクラス名は `Test` + 対象クラス名 | `TestExcelFile`, `TestCsvReader` |
| テストメソッド名は `test_` + 何を確認するか | `test_returns_none_when_not_found` |
| 一時ファイルは `tmp_path` フィクスチャを使う | `def test_something(tmp_path):` |

---

## プロジェクトセットアップファイル

新しいプロジェクトを作るときに毎回用意するファイル。

### ERRORS.md

非エンジニアがエラー画面のエラー名から対処を引ける表。
comken リポジトリの `ERRORS.md`（雛形）をプロジェクトルートにコピーし、
「プロジェクト固有のエラー」の表にそのプロジェクトで起きやすいエラーを追記していく。

### .gitignore

```gitignore
# 認証情報・環境設定（絶対に git に含めない）
config.ini
.env

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.venv/
*.egg-info/
dist/
build/

# ログ・一時ファイル
logs/
*.log
```

### pyproject.toml（Ruff 設定）

comken ライブラリ自体の `pyproject.toml` とは別に、プロジェクト側でも Ruff の設定を置く。

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I"]  # E=style, F=pyflakes, W=warning, I=import order
ignore = []
```

### requirements.txt

> **オフライン環境（社内BO環境）では `pip install -r requirements.txt` は使えない。**
> インターネット接続がある環境でのみ有効。社内ではライブラリを別途用意する必要がある。
> 参照用・記録用として維持する。

```
comken
openpyxl
selenium
simple-salesforce
pywin32
```

### config.ini.example

config.ini には**機密情報・個人情報を書かない**。URL・フォルダパス・フラグ等のみ。
パスワード・トークン・ユーザー名・メールアドレスなど、個人情報になりそうなものはすべて `python -m comken.credentials` で登録する（Windows DPAPI で暗号化される）。

```ini
; このファイルをコピーして config.ini を作成し、実際の値を入力する
; config.ini は .gitignore に含まれており git に push されない
; ※ 認証情報・個人情報はここに書かず python -m comken.credentials で登録する
; ※ セクション名・キー名は大文字で書く

[CREDENTIALS]
SALESFORCE = salesforce

[BROWSER]
; HEADLESS = True にするとブラウザ画面が表示されない
HEADLESS = False

[REPORT]
OUTPUT_FOLDER = C:\Users\Public\Downloads
```

---

## 開発環境（VS Code）

### 推奨拡張機能

`.vscode/extensions.json` をリポジトリに含めておくと、他の人が開いたときに自動でインストールを促せる。

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylance",
    "charliermarsh.ruff"
  ]
}
```

| 拡張機能 | 役割 |
|---|---|
| `ms-python.python` | Python 実行・デバッグ |
| `ms-python.pylance` | 型チェック・補完（Pyright ベース） |
| `charliermarsh.ruff` | リント・フォーマット（本規約準拠） |

### VS Code 設定

`.vscode/settings.json` をリポジトリに含める。

```json
{
  "python.defaultInterpreterPath": ".venv/Scripts/python.exe",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "ruff.enable": true,
  "editor.rulers": [100]
}
```

| 設定 | 効果 |
|---|---|
| `editor.formatOnSave` | 保存時に自動フォーマット |
| `source.fixAll.ruff` | 保存時にリント違反を自動修正 |
| `source.organizeImports.ruff` | 保存時に import を自動整理 |
| `editor.rulers` | 100文字の目安ラインを表示 |

### デバッグ設定

`.vscode/launch.json` でデバッグ実行の設定を書いておく。

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "main.py を実行",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}"
    }
  ]
}
```
