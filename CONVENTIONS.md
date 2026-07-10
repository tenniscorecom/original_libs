# コーディング規約

comken ライブラリおよびこのライブラリを使うプロジェクトで共通して使うルール。
Python 初学者でも読めるよう、ルールの「理由」も一緒に書いている。

---

---

## 目次

1. [基本方針](#基本方針)
2. [パッケージ・ファイル構成](#パッケージファイル構成)
3. [公開 API の管理](#公開-api-の管理)
4. [型ヒント](#型ヒント)
5. [定数とマジックナンバー](#定数とマジックナンバー)
6. [設定クラスのパターン](#設定クラスのパターン)
7. [リソース管理（with 文）](#リソース管理with-文)
8. [例外](#例外)
9. [Page Object Model](#page-object-model)
10. [循環インポートの解決](#循環インポートの解決)
11. [テスト](#テスト)
12. [コメント](#コメント)

---

## 基本方針

- **Ruff** に準拠する（PEP 8）
- **型ヒント**を必ず書く
- **マジックナンバー禁止**。数値・文字列定数は名前付き定数にする
- コメントは「なぜ」を書く。コードを読めば分かる「何を」は書かない

---

## パッケージ・ファイル構成

### comken ライブラリ自体の構造

```
comken/                     ← ライブラリのルート（パッケージ名）
  excel/
    __init__.py             ← 公開するクラスだけ re-export する
    handler.py              ← 実装本体
  csv/
    __init__.py
    handler.py
  browser/
    __init__.py
    base_page.py
    site_page.py
    driver.py
    options.py
  utils/
    __init__.py
    file.py                 ← ファイル操作（dated_filename, find_today_file 等）
    data.py                 ← データ操作（diff_rows 等）
  exceptions.py             ← カスタム例外の定義
  config.py
  __init__.py
```

### comken を使うプロジェクト（実行スクリプト）の構造

```
my_project/
  main.py              ← エントリポイント。ルートに置く（python main.py で実行）
  config.ini           ← 設定ファイル。ルートに置く（.gitignore に追加して秘匿）
  config.ini.example   ← 設定のテンプレート（git に含める）
  src/
    config.py          ← AppConfig（comken.Config を継承）
    browser_options.py ← MyOptions（comken.BrowserOptions を継承）
    pages/             ← 画面クラス（SitePage を継承）
      app_page.py
      login_page.py
    excel/             ← Excel 処理
      sales.py
    salesforce/        ← Salesforce 連携
      sync.py
```

**ルールと理由:**

| ファイル | 場所 | 理由 |
|---|---|---|
| `main.py` | ルート | `python main.py` で直接実行できる。`Config()` がカレントディレクトリの `config.ini` を読むので自然に合う |
| `config.ini` | ルート | 非エンジニアが触りやすい。`main.py` と同じ階層なので上の階層を探しに行く必要がない |
| `config.ini.example` | ルート | 認証情報のテンプレート。git に含めてチームで共有する |
| `src/` 以下 | `src/` | コードだけ。エンジニアの管理領域 |

**`main.py` をルートに置く理由（`src/main.py` にしない理由）:**

`src/main.py` にすると、`config.ini` を読む際に `Config("../config.ini")` と上の階層を参照する必要が生じる。
コードは下の階層（`src/`）を参照するだけで完結するのが自然なので、エントリポイントはルートに置く。

### なぜ `utils/` をファイルごとに分けるのか

`utils.py` 1ファイルに全部詰め込むと、将来機能が増えたときに何がどこにあるか分からなくなる。
カテゴリごとにファイルを分けておけば、`utils/file.py`（ファイル操作）、`utils/data.py`（データ操作）と一目で分かる。

呼び出し側は `from comken.utils import dated_filename` と書くだけで使える（中のファイル構造は意識しなくていい）。

---

## 公開 API の管理

### `__all__` で公開範囲を明示する

```python
# comken/excel/__init__.py
from .handler import ExcelFile

__all__ = ["ExcelFile"]   # ← これが「このパッケージの公開API」
```

`__all__` を書くと `from comken.excel import *` したときに `ExcelFile` だけが取り込まれる。
書かないと内部の実装クラスも全部漏れ出てしまう。

### 内部ヘルパーには `_` プレフィックスを付ける

```python
class ExcelFile:
    def read_rows(self, sheet_name: str) -> list[tuple]:   # 公開メソッド
        ws = self._sheet(sheet_name)                        # 内部で使う
        ...

    def _sheet(self, sheet_name: str):   # _ で始まる = 外から直接呼ばないでという意味
        ...
```

`_sheet()` は `ExcelFile` の内部でしか使わないメソッド。
`_` を付けることで「これはライブラリの内部実装なので、外から呼ばないでください」という意図を伝える。
Python は強制的に隠すことはしないが、慣習として広く使われている。

---

## 型ヒント

### 書き方

```python
# 良い
def find_today_file(folder: str | Path, pattern: str = "*.xlsx") -> Path | None:
    ...

# 悪い（型が分からない）
def find_today_file(folder, pattern="*.xlsx"):
    ...
```

### なぜ書くのか

- IDE（VSCode 等）が補完・エラー検出をしてくれる
- 関数の使い方がコードを見るだけで分かる
- `mypy` や `pyright` で型の不整合を事前に発見できる

### よく使う型ヒント

```python
str | None          # 文字列または None
Path | str          # Path オブジェクトまたは文字列
list[dict]          # 辞書のリスト
dict[str, list]     # キーが文字列、値がリストの辞書
```

- `Optional[X]` より `X | None` を使う（Python 3.10 以降の書き方）
- `Any` は使わない（型チェックが無意味になる）

---

## 定数とマジックナンバー

### マジックナンバーとは

コードの中に突然出てくる意味不明な数値や文字列のこと。

```python
# 悪い例（マジックナンバー）
rows = f.read_rows("売上データ", min_row=2)
if f.size > 10485760:
    ...
```

`"売上データ"` や `2`、`10485760` が何を意味するか、コードだけでは分からない。

### 定数に名前を付ける

```python
# 良い例（名前付き定数）
SHEET_NAME = "売上データ"
HEADER_ROW = 1
LOCAL_COPY_THRESHOLD_MB = 10
LOCAL_COPY_THRESHOLD_BYTES = LOCAL_COPY_THRESHOLD_MB * 1024 * 1024

rows = f.read_rows(SHEET_NAME, min_row=HEADER_ROW + 1)
if f.size > LOCAL_COPY_THRESHOLD_BYTES:
    ...
```

### 定数の書き方ルール

- **大文字スネークケース**（`SHEET_NAME`, `MAX_RETRY`）
- ファイルの先頭またはクラスの先頭（メソッドより上）にまとめて書く
- 計算式が必要な定数は式のまま書く（`10 * 1024 * 1024` → 意味が伝わる）

---

## 設定クラスのパターン

### クラス変数でデフォルト値を管理する

```python
class BrowserOptions:
    DRIVER_PATH: str = r"C:\Users\Public\Documents\msedgedriver.exe"
    WAIT_SECONDS: int = 10
    DOWNLOAD_DIR: str = str(Path.home() / "Downloads" / "comken")
    HEADLESS: bool = False
```

### プロジェクト側でサブクラスを作って上書きする

```python
# プロジェクト側の browser_options.py
class MyOptions(BrowserOptions):
    HEADLESS = True                             # 上書きしたい項目だけ書く
    DOWNLOAD_DIR = r"\\nas-server\downloads"   # 他はデフォルト値が使われる
```

### config.ini に書くのはプロジェクト固有の値だけ

```ini
; 良い例（プロジェクト固有）
[salesforce]
username = user@example.com
security_token = xxxxxxxxxxxx

[report]
output_folder = \\nas-server\reports
```

```ini
; 悪い例（ライブラリのデフォルト値）
[browser]
driver_path = C:\Users\Public\Documents\msedgedriver.exe
wait_seconds = 10
```

ライブラリのデフォルト値は `BrowserOptions` クラスに書く。
config.ini はプロジェクトごとに異なる値（接続先・認証情報等）だけを書く場所。

---

## リソース管理（with 文）

ファイル・ドライバー・COM オブジェクトは必ず `with` 文で使う。

```python
# 良い（with 文）
with ExcelFile("data.xlsx") as f:
    rows = f.read_rows_as_dicts("Sheet1")
# ← ブロックを抜けると自動で close() が呼ばれる（例外が起きても確実に閉じる）
```

```python
# 悪い（手動 close）
f = ExcelFile("data.xlsx")
rows = f.read_rows_as_dicts("Sheet1")
f.close()   # ← 上の行で例外が起きると、この行は実行されない → ファイルが開きっぱなし
```

### なぜ重要か

Excel ファイルが開いたままになると、次に開こうとしたときに「ファイルが使用中」エラーになる。
`with` 文を使えばブロックを抜けた瞬間（例外が起きても）必ず `close()` が呼ばれる。

---

## 例外

### カスタム例外階層を使う

```python
# comken/exceptions.py
class OriginalLibsError(Exception): ...     # ライブラリ全体の基底例外
class ExcelError(OriginalLibsError): ...    # Excel 系のエラー
class SheetNotFoundError(ExcelError): ...   # 指定シートが見つからない
```

```python
# 良い（カスタム例外）
raise SheetNotFoundError(f"シート '{name}' が見つかりません")

# 悪い（素の例外）
raise ValueError(f"シート '{name}' が見つかりません")
```

### なぜカスタム例外を使うのか

呼び出し側で特定のエラーだけ catch できるようになる。

```python
try:
    with ExcelFile("data.xlsx") as f:
        rows = f.read_rows("存在しないシート")
except SheetNotFoundError as e:
    print("シートが見つかりません:", e)   # ← シートのエラーだけ個別に処理できる
except ExcelError as e:
    print("Excel エラー:", e)             # ← その他の Excel エラーはまとめて処理
```

`ValueError` では「どんな不正な値のエラーなのか」が分からない。カスタム例外は意味が明確。

---

## Page Object Model

ブラウザ操作は必ず Page Object パターンで書く。

### 継承の構造

```
BasePage    ← comken 提供。click / input / select / alert 等の「ブラウザ操作の道具箱」
  └── SitePage    ← comken 提供。BASE_URL / go() を追加
        └── AppPage    ← プロジェクトで作る。サイト共通処理（ヘッダー操作等）
              └── LoginPage / DashboardPage / ...    ← 各画面クラス
```

### AppPage（サイト共通ベースクラス）の書き方

```python
# pages/app_page.py
from comken.browser.site_page import SitePage

class AppPage(SitePage):
    BASE_URL = "https://example.com"   # サイトのルート URL

    def get_flash_message(self) -> str:
        """全画面共通のフラッシュメッセージを取得する。"""
        return self.text_css("#flash")
```

### 各画面クラスの書き方

```python
# pages/login_page.py
class LoginPage(AppPage):
    # セレクター定数はクラス上部に大文字でまとめる（F12 で確認した値）
    PATH = "/login"
    USERNAME_ID = "username"
    PASSWORD_ID = "password"
    LOGIN_BTN_CSS = ".radius"

    def open(self) -> None:
        """ログイン画面を開く。"""
        self.go(self.PATH)   # BASE_URL + PATH に遷移

    def login(self, username: str, password: str) -> DashboardPage:
        """ログインして DashboardPage を返す。"""
        from .dashboard_page import DashboardPage   # 循環インポート対策

        self.input_id(self.USERNAME_ID, username)
        self.input_id(self.PASSWORD_ID, password)
        self.click_css(self.LOGIN_BTN_CSS)
        return DashboardPage(self._driver)   # ← 遷移先のページクラスを返す
```

### なぜ遷移メソッドはページクラスを返すのか

```python
# 返り値なし（悪い例）
login_page.login("user", "pass")
dashboard = DashboardPage(d.driver)   # ← 呼び出し側が次のページを自分で作る必要がある

# 返り値あり（良い例）
dashboard = login_page.login("user", "pass")   # ← 次の画面が自然に手に入る
title = dashboard.get_title()                   # ← そのまま操作できる
```

コードの流れが「ログインしたら次は dashboard」と一目で追えるようになる。

---

## 循環インポートの解決

2つの画面クラスが互いを参照するとき（`LoginPage` → `DashboardPage`、`DashboardPage` → `LoginPage`）に発生する。

### 解決パターン（`TYPE_CHECKING` + lazy import）

```python
from __future__ import annotations   # ① 全ての型注釈を文字列として扱う（実行時評価しない）
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # ② IDE 補完・型チェック用。ランタイムでは import されない（= 循環しない）
    from .dashboard_page import DashboardPage

class LoginPage(AppPage):
    def login(self, username: str, password: str) -> DashboardPage:   # ① のおかげで文字列扱い
        # ③ 実際に DashboardPage が必要になる場所でだけ import する
        from .dashboard_page import DashboardPage

        self.click_css(self.LOGIN_BTN_CSS)
        return DashboardPage(self._driver)
```

### なぜこの3つが全部必要か

| 方法 | IDE補完 | 実行時 |
|---|---|---|
| `TYPE_CHECKING` のみ | ○ | エラー（`DashboardPage` が未定義） |
| lazy import のみ | × | ○ |
| **両方** | **○** | **○** |

- `①` `from __future__ import annotations` がないと、`-> DashboardPage` の部分でも import が走ってしまう
- `②` `TYPE_CHECKING` ブロックは型チェッカーだけが読む（実行時は `TYPE_CHECKING = False` なのでスキップ）
- `③` lazy import で実行時に必要なタイミングだけ import する

---

## テスト

### ファイル構成

```
tests/
  __init__.py
  test_excel.py
  test_csv.py
  test_utils.py
  test_exceptions.py
```

### 書き方

```python
import pytest

class TestDatedFilename:
    """dated_filename のテスト。"""

    def test_default_prefix(self):
        """デフォルト（プレフィックスあり）のファイル名フォーマットを確認する。"""
        result = dated_filename("レポート")
        today = datetime.date.today().strftime("%Y%m%d")
        assert result == f"{today}_レポート.xlsx"

    def test_suffix_mode(self):
        """pre=False にするとサフィックスになることを確認する。"""
        result = dated_filename("レポート", pre=False)
        today = datetime.date.today().strftime("%Y%m%d")
        assert result == f"レポート_{today}.xlsx"
```

- テストクラス名は `Test対象クラス名`
- テストメソッド名は `test_何を確認するか`（日本語 docstring で補足）
- 一時ファイルは `pytest` の `tmp_path` フィクスチャを使う

```python
def test_find_today_file(tmp_path):
    """今日の日付を含むファイルが見つかることを確認する。"""
    today = datetime.date.today().strftime("%Y%m%d")
    (tmp_path / f"{today}_売上.xlsx").touch()
    result = find_today_file(tmp_path)
    assert result is not None
```

---

## コメント

### 書くべきコメント

「なぜこうしているか」が明らかでない場合だけ書く。

```python
# NAS 上の大きなファイルを直接開くと遅い・不安定なため、ローカルにコピーしてから開く
if src.stat().st_size > threshold:
    shutil.copy2(src, tmp_path)
```

```python
# 社内ルールでローカルコピーが不可の場合はこのブロックを丸ごと削除する
```

### 書かなくていいコメント

コードを読めば分かることは書かない。

```python
# 悪い例
i = i + 1   # i に 1 を加算する
rows = f.read_rows(SHEET)   # シートから行を読み込む
```
