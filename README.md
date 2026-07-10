# original_libs

業務自動化で使う Python 共通ライブラリ。

- コーディング規約: [CONVENTIONS.md](CONVENTIONS.md)
- エラーが出たときの対応: [ERRORS.md](ERRORS.md)（プロジェクトに配る雛形）

## モジュール一覧

| モジュール | 概要 |
|---|---|
| [Config](#config) | INI ファイルの読み込み |
| [認証情報（credentials）](#認証情報credentials) | パスワード等の暗号化保存（Windows DPAPI） |
| [CSV](#csv) | CSV の読み込み・検索・抽出 |
| [Excel（openpyxl）](#excel) | Excel の読み書き（数式・マクロは自動で win32com を使用） |
| [Windows（pywin32）](#windows) | Excel COM 操作・ウィンドウ操作・レジストリ読み取り |
| [Browser（Edge）](#browser) | Edge ブラウザ操作 |
| [Salesforce](#salesforce) | レコード CRUD・レポート取得 |

---

## セットアップ

```bash
pip install -r requirements.txt
```

---

## Config

`config.ini` を `config.SECTION.KEY` の形式で読み込む。

```python
from comken.config import Config

config = Config() # カレントディレクトリの config.ini
config = Config("path/to/config.ini") # パスを指定する場合
```

```ini
; config.ini（プロジェクト固有の非機密設定を書く）
; パスワード等の機密情報は書かない → 認証情報（credentials）を使う
; セクション名・キー名は大文字で書く（固定値と分かる + Python 側と表記が一致する）
[CREDENTIALS]
SALESFORCE = salesforce

[REPORT]
OUTPUT_FOLDER = \\nas-server\reports
TEMPLATE_PATH = \\nas-server\templates\template.xlsx
```

```python
config.CREDENTIALS.SALESFORCE # → str
config.REPORT.OUTPUT_FOLDER # → str
config.REPORT.TEMPLATE_PATH # → str
```

**プロジェクト固有の設定を追加する場合は Config を継承する:**

```python
class AppConfig(Config):
    @property
    def add_args(self) -> list[str]:
        return self.parse_list(self.BROWSER_OPTIONS.ADD)

config = AppConfig()
```

---

## 認証情報（credentials）

パスワード・トークン・ユーザー名などの機密情報・個人情報を Windows DPAPI で暗号化して保存する。
config.ini には機密情報を書かず、このモジュールを使う。

**仕組み:**

- 保存先は `%USERPROFILE%\.comken\credentials.dat`（プロジェクト内には置かない）
- Windows がログオン中のアカウントに紐付けて暗号化する。鍵の管理は不要
- 同じ「ユーザー × PC」でないと復号できない。ファイルをコピーされても読まれない
- 逆に言うと、**実行する PC ごとに登録が必要**（別の PC やサーバーで実行する場合はそこでも登録する）
- 1ユーザーにつき1ファイルで、キー名1つに値1つを何件でも登録できる
- 「ユーザー名とパスワードが必ずセット」という決め打ちはしない。パスワードだけのシステムにも対応できる

### 登録・削除（対話式ツール）

非エンジニアでも使える。起動してメニューを選ぶだけ。

```
> python -m comken.credentials
=== comken 認証情報の管理 ===

登録済みのキー名:
  oju_sys_password

1: 登録（新規追加・上書き）
2: 削除
q: 終了
選択: 1

システム名（例: salesforce）: salesforce
salesforce は新しいシステム名です。この名前で登録しますか？（y で続行）: y
項目名（例: username / password / token。空 Enter で終了）: username
値（入力しても画面には表示されません）:
値（確認のためもう一度）:
保存しました: salesforce_username
項目名（例: username / password / token。空 Enter で終了）: password
値（入力しても画面には表示されません）:
値（確認のためもう一度）:
保存しました: salesforce_password
項目名（例: username / password / token。空 Enter で終了）: ← 空 Enter で終了
保存先: C:\Users\xxx\.comken\credentials.dat
```

- **システム名は1回だけ入力**し、項目（username / password / token…）を続けて登録できる。
  項目ごとにシステム名を打ち直さないので「password のときだけスペルミス」が起きない
- 新しいシステム名のときは確認が入る（既存システムに追加するつもりのタイプミスに気づける）
- 既存のシステム名なら登録済みの項目一覧が表示される
- 同じキー名なら「上書き（＝変更）」になる。パスワードを変えたいときも同じ名前で登録し直せばよい
- 値は打ち間違い防止のため2回入力する（画面には表示されない）

### コードからの利用

まとめて使う場合は `Credentials` にプレフィックスを渡して属性で取り出す（キー名の直書きを避けられる）。

```python
from comken.credentials import Credentials

sf = Credentials("salesforce")
sf.username # → salesforce_username の値
sf.password # → salesforce_password の値
```

1件だけなら `load_credential` を使う。

```python
from comken.credentials import load_credential

password = load_credential("oju_sys_password")
```

未登録のキー名を指定すると `CredentialNotFoundError` になる（登録コマンドを案内するメッセージ付き）。

### キー名の付け方

| ルール | 例 |
|---|---|
| `システム名_項目名` の形式にする | `salesforce_password`, `oju_sys_password` |
| アカウントを使い分けるときはシステム名に用途を含める | `salesforce_test_password` |

キー名に使えるのは**半角英数字とアンダースコアのみ**。
それ以外（漢字・スペース・記号）は `InvalidCredentialNameError` で弾かれる。

どのシステム名（プレフィックス）を使うかはプロジェクトの config.ini の `[CREDENTIALS]` セクションに書く（キー名は機密ではない）:

```ini
[CREDENTIALS]
SALESFORCE = salesforce
```

```python
sf = Credentials(config.CREDENTIALS.SALESFORCE)
sf.username, sf.password, sf.token
# SALESFORCE = salesforce_test に変えるだけで全項目がテスト用に切り替わる
```

### 必要な項目の宣言（まとめて登録）

プロジェクトのコード側で「使う認証情報」を宣言しておくと、
CLI をプロジェクトのフォルダで起動したときに「3: まとめて登録」メニューが出る。

```python
# src/config.py（プロジェクト側で宣言する）
REQUIRED_CREDENTIALS = {
    "SALESFORCE": ["username", "password", "token"],  # キーは config.ini [CREDENTIALS] のキー名
    "OJU_SYS": ["password"],
}
```

```
選択: 3

このプロジェクトが使う認証情報（コード内の REQUIRED_CREDENTIALS 宣言）:
  oju_sys_password: 登録済み
  salesforce_password: 未登録
  salesforce_token: 未登録
  salesforce_username: 未登録

未登録の 3 件を順番に登録します（中断は Ctrl+C）。

--- salesforce_username ---
値（入力しても画面には表示されません）:
値（確認のためもう一度）:
保存しました: salesforce_username
...
```

- **キー名を1文字も打たずに登録できる**ので、スペルミスの余地がない
- プレフィックスは config.ini の `[CREDENTIALS]` から解決される
  （`SALESFORCE = salesforce_test` にすると要求されるキーもテスト用に変わる）
- 宣言はコードの一部としてエンジニアが管理する。宣言にない項目もメニュー1で自由に登録できる
- CLI は宣言を AST で読み取るだけで、プロジェクトのコードを実行しない

---

## CSV

```python
from comken.csv.handler import CsvReader

ORDER_ID = "A001"
STAFF_NAME = "山田"

reader = CsvReader("data.csv")
# Shift-JIS の場合: CsvReader("data.csv", encoding="cp932")

# 全行取得
rows = reader.rows()
# → [{"注文番号": "A001", "金額": "1000"}, ...]

# 特定列のみ取得
rows = reader.rows(columns=["注文番号", "金額"])

# キーで1件検索（見つからなければ None）
row = reader.find("注文番号", ORDER_ID)

# キーで複数行検索
rows = reader.filter("担当者", STAFF_NAME)

# 列の値一覧
amounts = reader.column("金額")
# → ["1000", "2000", "3000"]

# キー列でインデックス化（突合用）
lookup = reader.index("注文番号")
# → {"A001": {...}, "A002": {...}}
```

---

## ファイル名・ファイル取得ユーティリティ

```python
from comken.utils import FileFinder, FileNameBuilder

FOLDER = r"\\nas-server\share"

# 今日の日付付きファイル名を組み立てる
FileNameBuilder("売上レポート").plain()                # → "売上レポート.xlsx"
FileNameBuilder("売上レポート").prefix()               # → "20260711_売上レポート.xlsx"
FileNameBuilder("売上レポート").suffix()               # → "売上レポート_20260711.xlsx"
FileNameBuilder("ログ", ext=".csv").prefix()           # → "20260711_ログ.csv"
FileNameBuilder("月次レポート").prefix(date_format="%Y%m") # → "202607_月次レポート.xlsx"

# 今日の日付を含むファイルを取得
path = FileFinder(FOLDER).today()                      # YYYYMMDD で探す
path = FileFinder(FOLDER).today(date_format="%Y%m")    # YYYYMM で探す
if path is None:
    raise FileNotFoundError("今日のファイルが見つかりません")

# フォルダ内で最も新しいファイルを取得
path = FileFinder(FOLDER).latest()
path = FileFinder(FOLDER).latest(pattern="*.csv") # CSV に絞る場合
```

---

## ネットワーク・NAS ファイルの読み込み

NAS やネットワークドライブ上のファイルは直接開くと遅い・不安定になる場合がある。

### ExcelFile（openpyxl）

`local_copy_threshold_mb` を超えるファイルは自動でローカルにコピーしてから開く。
`with` ブロックを抜けるとテンポラリファイルは自動削除される。

```python
from comken.excel.handler import ExcelFile

NAS_PATH = r"\\nas-server\share\data.xlsx"
SHEET = "Sheet1"

# 10MB 以上は自動でローカルコピー（デフォルト）
with ExcelFile(NAS_PATH) as f:
    rows = f.read_rows_as_dicts(SHEET)

# 閾値を変える（50MB 以上でコピー）
with ExcelFile(NAS_PATH, local_copy_threshold_mb=50) as f:
    rows = f.read_rows_as_dicts(SHEET)

# ローカルコピーを無効化（社内ルールで不可の場合）
with ExcelFile(NAS_PATH, local_copy_threshold_mb=0) as f:
    rows = f.read_rows_as_dicts(SHEET)
```

### ExcelComHandler（win32com）

win32com は `ExcelFile` の自動コピー機能がないため、`local_copy` を使う。

```python
from comken.utils import local_copy
from comken.windows.handler import ExcelComHandler

NAS_PATH = r"\\nas-server\share\data.xlsx"
SHEET = "Sheet1"

with local_copy(NAS_PATH) as local_path:
    with ExcelComHandler(local_path) as h:
        rows = h.read_rows_as_dicts(SHEET)
```

---

## Excel

数式の計算結果や VBA マクロが必要な場合は自動で win32com にフォールバックする。

```python
from comken.excel.handler import ExcelFile

SHEET = "Sheet1"
ROW = 2
COL = 1
MACRO_NAME = "Module1.UpdateData"

# 読み取り
with ExcelFile("data.xlsx") as f:
    rows = f.read_rows(SHEET) # タプルのリスト
    rows = f.read_rows_as_dicts(SHEET) # 辞書のリスト（ヘッダーをキーに）

# 数式の計算結果を読む（openpyxl → win32com 自動フォールバック）
with ExcelFile("data.xlsx") as f:
    rows = f.read_computed_rows(SHEET)

# 書き込み・保存
with ExcelFile("data.xlsx") as f:
    f.write_cell(SHEET, row=ROW, col=COL, value="値")
    f.save()
    f.save("output.xlsx") # 別名で保存

# 大量データの読み取り（メモリ効率優先）
with ExcelFile("data.xlsx") as f:
    for row in f.iter_rows(SHEET):
        print(row) # 1行ずつ処理。全行をメモリに乗せない

# 複数ファイルを同時処理する場合（目安: 10ファイル以上）は
# concurrent.futures.ThreadPoolExecutor を使うと高速化できる

# 背景色の設定
YELLOW = "FFFF00"
RED = "FF0000"

with ExcelFile("data.xlsx") as f:
    f.set_fill(SHEET, row=ROW, col=COL, color=YELLOW) # 黄色
    f.set_fill(SHEET, row=ROW, col=COL, color=RED)    # 赤
    f.save()

# VBA マクロの実行（常に win32com を使用）
with ExcelFile("data.xlsm") as f:
    f.run_macro(MACRO_NAME)
```

---

## Windows

通常の Excel 読み書きは ExcelFile（openpyxl）を使うこと。
ExcelComHandler は数式・マクロ・パスワード保存が必要な場合に限定して使う。

### ExcelComHandler

```python
from comken.windows.handler import ExcelComHandler

SHEET = "Sheet1"
DATA_ROW = 2
DATA_COL = 3
CHECK_ROW = 5
MACRO_NAME = "Module1.UpdateData"
READ_PW = "読み取りPW"
WRITE_PW = "書き込みPW"

with ExcelComHandler("data.xlsx") as h:
    value = h.read_cell(SHEET, row=DATA_ROW, col=DATA_COL)
    rows = h.read_rows(SHEET)
    rows = h.read_rows_as_dicts(SHEET)
    last_row = h.used_last_row(SHEET)

    if h.count_a(SHEET, row=CHECK_ROW) == 0:
        print(f"{CHECK_ROW}行目は空行")

    h.run_macro(MACRO_NAME)
    h.save_as("output.xlsx", read_pw=READ_PW, write_pw=WRITE_PW)
```

### WindowHandler

```python
from comken.windows.handler import WindowHandler

WINDOW_TITLE = "メモ帳"

w = WindowHandler(WINDOW_TITLE)
w.activate() # ウィンドウを前面に表示
w.get_title() # タイトルを取得
```

### RegistryHandler

```python
import win32con
from comken.windows.handler import RegistryHandler

SETTING_KEY = "SettingName"

with RegistryHandler(win32con.HKEY_CURRENT_USER, r"Software\MyApp") as r:
    value = r.read(SETTING_KEY)
```

---

## Browser

### EdgeDriver

```python
from comken.browser.driver import EdgeDriver

URL = "https://example.com"

# デフォルト設定のまま起動
with EdgeDriver() as d:
    d.driver.get(URL)
```

**ブラウザオプションのカスタマイズ:**

デフォルト設定は `comken/browser/options.py` の `BrowserOptions` を参照。
変更したい項目だけサブクラスで上書きする。`DRIVER_PATH` と `WAIT_SECONDS` もここで変更する。

```python
# browser_options.py（プロジェクト側）
from comken.browser.options import BrowserOptions

class MyOptions(BrowserOptions):
    DRIVER_PATH = r"C:\tools\msedgedriver.exe" # ドライバーパスを変更する場合
    WAIT_SECONDS = 15 # 待機秒数を変更する場合
    INCOGNITO = False # シークレットモードを無効
    START_MAXIMIZED = False # 最大化を無効（WINDOW_SIZE と併用不可）
    WINDOW_SIZE = "1600,1024"
```

```python
with EdgeDriver(browser_options=MyOptions()) as d:
    ...
```

デフォルト一覧の確認:

```python
print(BrowserOptions()) # デフォルト設定を表示
print(MyOptions()) # デフォルトからの変更箇所に * が付く
```

---

### BasePage

画面ごとに `BasePage` を継承したクラスを作る。

```python
from comken.browser.base_page import BasePage

class LoginPage(BasePage):
    URL = "https://example.com/login"
    USERNAME_ID = "username"
    PASSWORD_ID = "password"
    LOGIN_BTN_ID = "login-btn"

    def open(self) -> None:
        self._driver.get(self.URL)

    def login(self, username: str, password: str) -> None:
        self.input_id(self.USERNAME_ID, username)
        self.input_id(self.PASSWORD_ID, password)
        self.click_id(self.LOGIN_BTN_ID)
```

**セレクター別メソッド一覧:**

| 操作 | ID | name属性 | CSSセレクター | XPath |
|---|---|---|---|---|
| クリック | `click_id` | `click_name` | `click_css` | `click_xpath` |
| テキスト入力 | `input_id` | `input_name` | `input_css` | `input_xpath` |
| テキスト取得 | `text_id` | `text_name` | `text_css` | `text_xpath` |
| プルダウン（テキスト） | `select_text_id` | `select_text_name` | `select_text_css` | `select_text_xpath` |
| プルダウン（value） | `select_value_id` | `select_value_name` | `select_value_css` | `select_value_xpath` |
| プルダウン（番号） | `select_index_id` | `select_index_name` | `select_index_css` | `select_index_xpath` |
| 要素が出るまで待つ | `wait_visible_id` | — | `wait_visible_css` | `wait_visible_xpath` |
| 要素が消えるまで待つ | — | — | `wait_invisible_css` | `wait_invisible_xpath` |
| 要素の存在チェック | `has_id` | — | `has_css` | `has_xpath` |
| スクロール（要素まで） | `scroll_to_id` | — | `scroll_to_css` | — |

**セレクター不要のメソッド:**

| メソッド | 用途 |
|---|---|
| `select_radio_name(name, value)` | ラジオボタンを name + value で選択 |
| `alert_accept()` | アラートを OK する |
| `alert_dismiss()` | アラートをキャンセルする |
| `alert_text()` | アラートのテキストを取得 |
| `scroll_bottom()` | ページ最下部へスクロール |
| `drag_drop_css(source, target)` | ドラッグ＆ドロップ |
| `js(script, *args)` | JavaScript を実行 |
| `save_screenshot(prefix)` | スクリーンショットを保存 |

セレクターの値は Edge の開発者ツール（F12）で確認する。

---

### サンプル実装

`examples/sample_login/` に動作するサンプルがある。

```
examples/sample_login/
├── pages/
│   ├── login_page.py # ログイン画面
│   └── secure_page.py # ログイン後の画面
├── browser_options.py # BrowserOptions のカスタマイズ
├── config.ini.example # 設定ファイルのテンプレート
├── config.py # AppConfig（Config のサブクラス）
└── run.py # 実行スクリプト
```

実行:

```bash
cd F:\dev\original_libs
python -m examples.sample_login.run
```

---

## Salesforce

### SalesforceClient（simple-salesforce）

```python
from comken.credentials import Credentials
from comken.salesforce.simple_sf import SalesforceClient

# 事前に python -m comken.credentials で登録しておく
cred = Credentials("salesforce") # 本番・テストの切り替えは config.ini のプレフィックスで
sf = SalesforceClient(
    username=cred.username,
    password=cred.password,
    security_token=cred.token,
    # domain="test" # Sandbox の場合
)

SOQL = "SELECT Id, Name FROM Account WHERE IsDeleted = false"
EXTERNAL_ID = "001"

records = sf.query(SOQL)
new_id = sf.insert("Account", {"Name": "新規取引先"})
sf.update("Account", record_id=new_id, data={"Name": "更新後の名前"})
sf.upsert("Account", external_id_field="ExternalId__c", data={"ExternalId__c": EXTERNAL_ID, "Name": "取引先"})
sf.delete("Account", record_id=new_id)
```

### SalesforceRestClient（REST API）

```python
from comken.salesforce.rest_api import SalesforceRestClient

sf = SalesforceRestClient.from_password(
    username="user@example.com",
    password="password",
    security_token="トークン",
    client_id="クライアントID",
    client_secret="クライアントシークレット",
)

SOQL = "SELECT Id, Name FROM Account"
ACCOUNT_NAME = "新規取引先"
ACCOUNT_NAME_UPDATED = "更新後"

records = sf.query(SOQL)
new_id = sf.insert("Account", {"Name": ACCOUNT_NAME})
sf.update("Account", record_id=new_id, data={"Name": ACCOUNT_NAME_UPDATED})
sf.delete("Account", record_id=new_id)
```

### SalesforceReportClient（レポート取得）

```python
from comken.salesforce.report import SalesforceReportClient

sf = SalesforceReportClient(
    instance_url="https://xxx.salesforce.com",
    access_token="アクセストークン",
)

REPORT_ID = "00O000000000001"
START_DATE = "2026-01-01"

# 2000行以下（同期）
rows = sf.run(REPORT_ID)
# → [{"取引先名": "株式会社A", "金額": "100,000"}, ...]

# 2000行超え（非同期）
rows = sf.run_async(REPORT_ID)

# 絞り込みあり
rows = sf.run(REPORT_ID, filters=[
    {"column": "CREATED_DATE", "operator": "greaterThan", "value": START_DATE},
])
```

レポート ID は Salesforce でレポートを開いたときの URL から確認できる:
`https://xxx.salesforce.com/00O000000000001`

---

## パッケージ構成

```mermaid
graph LR
    comken --> config["Config\n設定ファイル"]
    comken --> credentials["credentials\n認証情報の暗号化"]
    comken --> utils["utils\nファイル操作・比較"]
    comken --> excel["excel\nExcel"]
    comken --> csv["csv\nCSV"]
    comken --> windows["windows\nCOM / Window"]
    comken --> browser["browser\nブラウザ"]
    comken --> salesforce["salesforce\nSalesforce"]
```

---

## 主なユースケース

### NAS の Excel を読んで加工・出力する

```mermaid
flowchart LR
    A["NAS\nExcel"] -->|FileFinder.today| B["ファイルパス取得"]
    B -->|ExcelFile| C["データ読み込み"]
    C --> D["データ加工"]
    D -->|write_cell + save| E["Excel出力"]
```

### CSV を読んで Excel レポートを作る

```mermaid
flowchart LR
    A["CSVファイル"] -->|CsvReader| B["データ読み込み"]
    B -->|filter / index| C["絞り込み・突合"]
    C -->|ExcelFile| D["Excel書き込み"]
    D --> E["レポート完成"]
```

### Salesforce のデータを Excel に出力する

```mermaid
flowchart LR
    A["Salesforce"] -->|SalesforceReportClient| B["レポート取得"]
    B --> C["データ加工"]
    C -->|ExcelFile| D["Excel出力"]
```

### ブラウザを自動操作する

```mermaid
flowchart LR
    A["config.ini"] -->|Config| B["設定読み込み"]
    B -->|EdgeDriver| C["ブラウザ起動"]
    C -->|SitePage| D["画面操作"]
```

---

## 改訂履歴

| 日付 | 内容 |
|---|---|
| 2026-07-09 | 初版作成 |
| 2026-07-10 | 全モジュールにドキュメント追加、README 整理 |
| 2026-07-11 | credentials モジュール追加（認証情報の暗号化保存・管理ツール） |
