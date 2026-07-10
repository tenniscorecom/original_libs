# original_libs

業務自動化で使う Python 共通ライブラリ。

## モジュール一覧

| モジュール | 概要 |
|---|---|
| [Config](#config) | INI ファイルの読み込み |
| [CSV](#csv) | CSV の読み込み・検索・抽出 |
| [Excel（openpyxl）](#excel) | Excel の読み書き（数式・マクロは自動で win32com を使用） |
| [Windows（pywin32）](#windows) | Excel COM 操作・ウィンドウ操作・レジストリ読み取り |
| [Selenium（Edge）](#selenium) | Edge ブラウザ操作 |
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
from src.config import Config

config = Config()                      # カレントディレクトリの config.ini
config = Config("path/to/config.ini")  # パスを指定する場合
```

```ini
; config.ini
[browser]
driver_path  = C:\Users\Public\Documents\msedgedriver.exe
wait_seconds = 10
headless     = false
```

```python
config.BROWSER.DRIVER_PATH    # → str
config.BROWSER.HEADLESS       # → False（bool に自動変換）
config.BROWSER.WAIT_SECONDS   # → "10"（数値は呼び出し側で変換）
int(config.BROWSER.WAIT_SECONDS)  # → 10
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

## CSV

```python
from src.csv.handler import CsvReader

reader = CsvReader("data.csv")
# Shift-JIS の場合: CsvReader("data.csv", encoding="cp932")

# 全行取得
rows = reader.rows()
# → [{"注文番号": "A001", "金額": "1000"}, ...]

# 特定列のみ取得
rows = reader.rows(columns=["注文番号", "金額"])

# キーで1件検索（見つからなければ None）
row = reader.find("注文番号", "A001")

# キーで複数行検索
rows = reader.filter("担当者", "山田")

# 列の値一覧
amounts = reader.column("金額")
# → ["1000", "2000", "3000"]

# キー列でインデックス化（突合用）
lookup = reader.index("注文番号")
# → {"A001": {...}, "A002": {...}}
```

---

## Excel

数式の計算結果や VBA マクロが必要な場合は自動で win32com にフォールバックする。

```python
from src.excel.handler import ExcelFile

# 読み取り
with ExcelFile("data.xlsx") as f:
    rows = f.read_rows("Sheet1")             # タプルのリスト
    rows = f.read_rows_as_dicts("Sheet1")    # 辞書のリスト（ヘッダーをキーに）

# 数式の計算結果を読む（openpyxl → win32com 自動フォールバック）
with ExcelFile("data.xlsx") as f:
    rows = f.read_computed_rows("Sheet1")

# 書き込み・保存
with ExcelFile("data.xlsx") as f:
    f.write_cell("Sheet1", row=2, col=1, value="値")
    f.save()
    f.save("output.xlsx")  # 別名で保存

# VBA マクロの実行（常に win32com を使用）
with ExcelFile("data.xlsm") as f:
    f.run_macro("Module1.UpdateData")
```

---

## Windows

通常の Excel 読み書きは ExcelFile（openpyxl）を使うこと。
ExcelComHandler は数式・マクロ・パスワード保存が必要な場合に限定して使う。

### ExcelComHandler

```python
from src.windows.handler import ExcelComHandler

with ExcelComHandler("data.xlsx") as h:
    value    = h.read_cell("Sheet1", row=2, col=3)
    rows     = h.read_rows("Sheet1")
    rows     = h.read_rows_as_dicts("Sheet1")
    last_row = h.used_last_row("Sheet1")

    if h.count_a("Sheet1", row=5) == 0:
        print("5行目は空行")

    h.run_macro("Module1.UpdateData")
    h.save_as("output.xlsx", read_pw="読み取りPW", write_pw="書き込みPW")
```

### WindowHandler

```python
from src.windows.handler import WindowHandler

w = WindowHandler("メモ帳")
w.activate()     # ウィンドウを前面に表示
w.get_title()    # タイトルを取得
```

### RegistryHandler

```python
import win32con
from src.windows.handler import RegistryHandler

with RegistryHandler(win32con.HKEY_CURRENT_USER, r"Software\MyApp") as r:
    value = r.read("SettingName")
```

---

## Selenium

### EdgeDriver

```python
from src.selenium.driver import EdgeDriver
from src.selenium.options import BrowserOptions

with EdgeDriver(driver_path=r"C:\Users\Public\Documents\msedgedriver.exe") as d:
    d.driver.get("https://example.com")
```

**ブラウザオプションのカスタマイズ:**

デフォルト設定は `src/selenium/options.py` の `BrowserOptions` を参照。
変更したい項目だけサブクラスで上書きする。

```python
# browser_options.py（プロジェクト側）
from src.selenium.options import BrowserOptions

class MyOptions(BrowserOptions):
    INCOGNITO = False           # シークレットモードを無効
    START_MAXIMIZED = False     # 最大化を無効（WINDOW_SIZE と併用不可）
    WINDOW_SIZE = "1600,1024"
```

```python
with EdgeDriver(
    driver_path=config.BROWSER.DRIVER_PATH,
    wait_seconds=int(config.BROWSER.WAIT_SECONDS),
    browser_options=MyOptions(),
) as d:
    ...
```

デフォルト一覧の確認:

```python
print(BrowserOptions())      # デフォルト設定を表示
print(MyOptions())           # デフォルトからの変更箇所に * が付く
```

---

### BasePage

画面ごとに `BasePage` を継承したクラスを作る。

```python
from src.selenium.base_page import BasePage

class LoginPage(BasePage):
    URL = "https://example.com/login"

    def open(self) -> None:
        self._driver.get(self.URL)

    def login(self, username: str, password: str) -> None:
        self.input_id("username", username)
        self.input_id("password", password)
        self.click_id("login-btn")
```

| 操作 | ID | name属性 | CSSセレクター | XPath |
|---|---|---|---|---|
| クリック | `click_id` | `click_name` | `click_css` | `click_xpath` |
| テキスト入力 | `input_id` | `input_name` | `input_css` | `input_xpath` |
| テキスト取得 | `text_id` | `text_name` | `text_css` | `text_xpath` |

セレクターの値は Edge の開発者ツール（F12）で確認する。

---

### サンプル実装

`examples/sample_login/` に動作するサンプルがある。

```
examples/sample_login/
├── pages/
│   ├── login_page.py    # ログイン画面
│   └── secure_page.py   # ログイン後の画面
├── browser_options.py   # BrowserOptions のカスタマイズ
├── config.ini.example   # 設定ファイルのテンプレート
├── config.py            # AppConfig（Config のサブクラス）
└── run.py               # 実行スクリプト
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
from src.salesforce.simple_sf import SalesforceClient

sf = SalesforceClient(
    username="user@example.com",
    password="password",
    security_token="セキュリティトークン",
    # domain="test"  # Sandbox の場合
)

records = sf.query("SELECT Id, Name FROM Account WHERE IsDeleted = false")
new_id  = sf.insert("Account", {"Name": "新規取引先"})
sf.update("Account", record_id=new_id, data={"Name": "更新後の名前"})
sf.upsert("Account", external_id_field="ExternalId__c", data={"ExternalId__c": "001", "Name": "取引先"})
sf.delete("Account", record_id=new_id)
```

### SalesforceRestClient（REST API）

```python
from src.salesforce.rest_api import SalesforceRestClient

sf = SalesforceRestClient.from_password(
    username="user@example.com",
    password="password",
    security_token="トークン",
    client_id="クライアントID",
    client_secret="クライアントシークレット",
)

records = sf.query("SELECT Id, Name FROM Account")
new_id  = sf.insert("Account", {"Name": "新規取引先"})
sf.update("Account", record_id=new_id, data={"Name": "更新後"})
sf.delete("Account", record_id=new_id)
```

### SalesforceReportClient（レポート取得）

```python
from src.salesforce.report import SalesforceReportClient

sf = SalesforceReportClient(
    instance_url="https://xxx.salesforce.com",
    access_token="アクセストークン",
)

# 2000行以下（同期）
rows = sf.run("00O000000000001")
# → [{"取引先名": "株式会社A", "金額": "100,000"}, ...]

# 2000行超え（非同期）
rows = sf.run_async("00O000000000001")

# 絞り込みあり
rows = sf.run("00O000000000001", filters=[
    {"column": "CREATED_DATE", "operator": "greaterThan", "value": "2026-01-01"},
])
```

レポート ID は Salesforce でレポートを開いたときの URL から確認できる:
`https://xxx.salesforce.com/00O000000000001`

---

## 改訂履歴

| 日付 | 内容 |
|---|---|
| 2026-07-09 | 初版作成 |
| 2026-07-10 | 全モジュールにドキュメント追加、README 整理 |
