# original_libs

業務自動化で使う Python 共通ライブラリ。

- [Selenium（Edge）](#selenium)
- [Excel（openpyxl）](#excel-openpyxl)
- [Windows（pywin32）](#windows-pywin32)
- [Salesforce](#salesforce)

---

## セットアップ

```bash
pip install -r requirements.txt
```

---

## Selenium

### EdgeDriver

```python
from src.selenium.driver import EdgeDriver

with EdgeDriver(driver_path=r"C:\Users\Public\Documents\msedgedriver.exe") as d:
    d.driver.get("https://example.com")
    print(d.driver.title)
# with を抜けると自動でブラウザが閉じる
```

| 引数 | 型 | デフォルト | 説明 |
|---|---|---|---|
| `driver_path` | str | 必須 | msedgedriver.exe のパス |
| `wait_seconds` | int | 10 | 暗黙的待機（秒） |
| `headless` | bool | False | True でブラウザを非表示 |

---

### BasePage

画面ごとに `BasePage` を継承したクラスを作る。`By.ID` などは不要。

```python
from src.selenium.base_page import BasePage

class LoginPage(BasePage):
    def login(self, user: str, password: str) -> None:
        self.input_id("username", user)
        self.input_id("password", password)
        self.click_id("login-btn")
```

```python
with EdgeDriver(driver_path=r"C:\...\msedgedriver.exe") as d:
    page = LoginPage(d.driver)
    page.open("https://example.com/login")
    page.login("yamada", "password123")
```

#### メソッド一覧

| 操作 | ID | name属性 | CSSセレクター | XPath |
|---|---|---|---|---|
| クリック | `click_id` | `click_name` | `click_css` | `click_xpath` |
| テキスト入力 | `input_id` | `input_name` | `input_css` | `input_xpath` |
| テキスト取得 | `text_id` | `text_name` | `text_css` | `text_xpath` |

```python
# 使用例
page.click_id("submit-btn")
page.click_css(".btn-primary")
page.click_xpath("//button[@type='submit']")

page.input_id("search", "キーワード")
page.input_css("#email", "test@example.com")

title = page.text_id("page-title")
```

| メソッド | 説明 |
|---|---|
| `open(url)` | URL を開く |
| `save_screenshot(prefix)` | スクリーンショットを `logs/` に保存 |

#### サンプル実装

`examples/sample_login/` に実際に動くサンプルがある。

```
examples/
└── sample_login/
    ├── pages/
    │   ├── login_page.py   # ログイン画面
    │   └── secure_page.py  # ログイン後の画面
    └── run.py              # 実行スクリプト
```

```python
# pages/login_page.py の例
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

```python
# run.py の例
from src.selenium.driver import EdgeDriver
from pages.login_page import LoginPage

with EdgeDriver(driver_path=r"C:\...\msedgedriver.exe") as d:
    page = LoginPage(d.driver)
    page.open()
    page.login("yamada", "password123")
```

実行:
```bash
cd F:\dev\original_libs
python -m examples.sample_login.run
```

---

## Excel（openpyxl）

数式の計算結果は読めない。数式を読む場合は [ExcelComHandler](#excelcomhandler) を使う。

```python
from src.excel.handler import ExcelFile

# 読み取り
with ExcelFile("data.xlsx") as f:
    rows = f.read_rows("Sheet1")  # [(値, 値, ...), ...]
    print(rows)

# 書き込み
with ExcelFile("data.xlsx") as f:
    f.write_cell("Sheet1", row=2, col=1, value="新しい値")
    f.save()

# 別名で保存
with ExcelFile("template.xlsx") as f:
    f.write_cell("Sheet1", 2, 1, "値")
    f.save("output.xlsx")

# 数式の計算結果を読む（キャッシュ値）
with ExcelFile("data.xlsx", data_only=True) as f:
    rows = f.read_rows("Sheet1")

# 大きなファイルを読み取り専用で開く
with ExcelFile("large.xlsx", read_only=True) as f:
    rows = f.read_rows("Sheet1")
```

| メソッド | 説明 |
|---|---|
| `sheet(name)` | Worksheet オブジェクトを返す |
| `read_rows(sheet_name, min_row=2)` | 2行目以降を全行読む |
| `write_cell(sheet_name, row, col, value)` | セルに値を書く |
| `save(path=None)` | 保存（省略時は元のパス） |

---

## Windows（pywin32）

### ExcelComHandler

数式の計算結果を読む・パスワード付きで保存する場合に使う。

```python
from src.windows.handler import ExcelComHandler

with ExcelComHandler("data.xlsx") as h:
    # 数式の計算結果を取得
    value = h.read_cell("T_data", row=2, col=17)

    # データを書き込む
    h.write_cell("T_data", row=2, col=1, value="書き込む値")

    # 最終行を取得
    last_row = h.used_last_row("T_data")

    # 行全体が空かどうか確認
    if h.count_a("T_data", row=3) == 0:
        print("空行")

    # パスワードをかけて保存
    h.save_as("output.xlsx", read_pw="読み取りPW", write_pw="書き込みPW")
# with を抜けると自動で Excel が閉じる
```

---

### WindowHandler

```python
from src.windows.handler import WindowHandler

w = WindowHandler("メモ帳")
w.activate()  # ウィンドウを前面に表示
print(w.get_title())
```

---

### RegistryHandler

```python
import win32con
from src.windows.handler import RegistryHandler

with RegistryHandler(win32con.HKEY_CURRENT_USER, r"Software\MyApp") as r:
    value = r.read("Setting")
    print(value)
```

---

## Salesforce

### SalesforceClient（simple-salesforce）

```python
from src.salesforce.simple_sf import SalesforceClient

sf = SalesforceClient(
    username="user@example.com",
    password="password",
    security_token="token",
)

# レコード取得
records = sf.query("SELECT Id, Name FROM Account WHERE IsDeleted = false")

# レコード作成
new_id = sf.insert("Account", {"Name": "新規取引先"})

# レコード更新
sf.update("Account", record_id=new_id, data={"Name": "更新後の名前"})

# Upsert（外部IDで更新 or 作成）
sf.upsert("Account", external_id_field="ExternalId__c", data={"ExternalId__c": "001", "Name": "取引先"})

# レコード削除
sf.delete("Account", record_id=new_id)
```

---

### SalesforceRestClient（REST API 直叩き）

```python
from src.salesforce.rest_api import SalesforceRestClient

# パスワード認証でインスタンス生成
sf = SalesforceRestClient.from_password(
    username="user@example.com",
    password="password",
    security_token="token",
    client_id="接続アプリケーションのClientId",
    client_secret="接続アプリケーションのClientSecret",
)

# または接続済みのトークンを直接渡す
sf = SalesforceRestClient(
    instance_url="https://xxx.salesforce.com",
    access_token="アクセストークン",
)

# レコード取得（全ページ自動取得）
records = sf.query("SELECT Id, Name FROM Account")

# レコード作成
new_id = sf.insert("Account", {"Name": "新規取引先"})

# レコード更新
sf.update("Account", record_id=new_id, data={"Name": "更新後の名前"})

# レコード削除
sf.delete("Account", record_id=new_id)
```

---

### SalesforceReportClient（レポート取得）

既存の Salesforce レポートを実行してデータを取得する。

```python
from src.salesforce.report import SalesforceReportClient

sf = SalesforceReportClient(
    instance_url="https://xxx.salesforce.com",
    access_token="アクセストークン",
)

# 2000行以下：同期実行
rows = sf.run("00O000000000001")
# → [{"取引先名": "株式会社A", "金額": "100,000"}, ...]
# 列名はSalesforceの表示名（日本語）で返る

# 2000行超え：非同期実行
rows = sf.run_async("00O000000000001")

# 絞り込みあり
rows = sf.run("00O000000000001", filters=[
    {"column": "CREATED_DATE", "operator": "greaterThan", "value": "2026-01-01"}
])
```

> **注意**: レポート ID は Salesforce でレポートを開いたときの URL から確認できる。
> `https://xxx.salesforce.com/00O000000000001`

| メソッド | 上限 | 説明 |
|---|---|---|
| `run(report_id, filters)` | 2000行 | 同期実行。小〜中規模レポート向け |
| `run_async(report_id, filters)` | 上限なし | 非同期実行。大規模レポート向け |

---

## 改訂履歴

| 日付 | 内容 |
|---|---|
| 2026-07-09 | 初版作成 |
