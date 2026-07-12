# examples — 動くサンプル集

comken の使い方を「動くコード」で覚えるためのサンプル。
どれもリポジトリのルートから `python -m examples.<フォルダ名>.run` で実行する。

## 一覧（学ぶ順のおすすめ）

| # | フォルダ | 内容 | 主に使うモジュール | 実行条件 |
|---|---|---|---|---|
| 1 | csv_to_excel_report | CSV を読んで Excel レポートを作る | CsvReader / ExcelFile / Sheet / Color | なし（同梱データで動く） |
| 2 | excel_key_transfer | マスタ CSV を Excel にキー突合転記（XLOOKUP 的転記） | CsvReader.index / transfer_by_key / diff_rows | なし（データを自動生成） |
| 3 | csv_diff_report | 昨日と今日の CSV の差分を色付き Excel レポートに | diff_rows / CsvWriter / set_fill | なし（データを自動生成） |
| 4 | sample_login | ブラウザ自動化（Page Object Model の一式） | EdgeDriver / BasePage / Locator | Edge + msedgedriver |
| 5 | salesforce_to_excel | Salesforce のデータを Excel に出力 | Credentials / SalesforceApiClient / Config | Salesforce 環境 + 認証情報の登録 |
| 6 | daily_batch_template | 日次バッチの雛形（新規プロジェクトのコピー元） | setup_logger / FileFinder / TeamsNotifier | config.ini の作成 |

## 実行方法

```bash
# 例: CSV → Excel レポート
python -m examples.csv_to_excel_report.run
```

- 1〜3 は外部システム・ネット接続なしでそのまま動く。出力は各フォルダの `output/` に入る
- 4〜6 は各フォルダの run.py 冒頭に書いてある事前準備を済ませてから実行する

## 新しいツールを作るときは

`daily_batch_template` をコピーして始めるのが早い。
「入力ファイルを探す → 加工する → Excel を出力する → Teams に通知する」という
実務でいちばん多い構成に、エラー処理・ログ・config.ini の書き方が入っている。

ブラウザ自動化のツールなら `sample_login` の pages/ 構成（Page Object Model）を合わせて使う。
