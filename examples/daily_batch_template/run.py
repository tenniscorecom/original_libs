"""
雛形: 日次バッチ（当日ファイルの取得 → Excel レポート → Teams 通知）

新しい自動化ツールを作るときは、このフォルダをコピーして始めると速い。
「入力ファイルを探す → 加工する → 出力する → 結果を通知する」という
実務でいちばん多い形に、ログとエラー処理の書き方をひととおり含めてある。

事前準備:
    このフォルダの config.ini.example をコピーして config.ini を作り、
    フォルダパス等を環境に合わせて書き換える。

実行方法:
    リポジトリのルートで python -m examples.daily_batch_template.run
    （実プロジェクトに移すときは main.py にリネームし、templates/実行.bat を組み合わせる）
"""

import logging

from comken import OriginalLibsError, TeamsError, setup_logger
from comken.csv import CsvReader
from comken.excel import ExcelFile
from comken.teams import CardColor, TeamsNotifier
from comken.utils import FileFinder, FileNameBuilder

from .config import config

SHEET = "Sheet1"
BATCH_NAME = "日次売上レポート"
INPUT_PATTERN = "*.csv"

logger = logging.getLogger(__name__)


def notify(title: str, body: str, color: str = CardColor.DEFAULT) -> None:
    """Teams に通知する。URL が未設定ならスキップし、送信に失敗しても本処理は止めない。"""
    if not config.TEAMS.WEBHOOK_URL:
        logger.info("Teams 通知はスキップ（WEBHOOK_URL 未設定）: %s", title)
        return
    try:
        TeamsNotifier(config.TEAMS.WEBHOOK_URL).send_card(title, body=body, color=color)
    except TeamsError:
        # 通知はあくまで付加機能。失敗しても本処理の結果（出力ファイル）は生きている
        logger.warning("Teams への通知に失敗しました（処理は続行）", exc_info=True)


def main() -> None:
    # 入力フォルダから「今日の日付が名前に入ったファイル」を探す。
    # required=False にすると見つからないとき None が返る（エラーにせずスキップ運用できる）
    source = FileFinder(config.FILES.INPUT_FOLDER).today(pattern=INPUT_PATTERN, required=False)
    if source is None:
        logger.info("本日分の入力ファイルがないため何もしません")
        return

    rows = CsvReader(source).rows()
    logger.info("読み込み: %s（%d 件）", source.name, len(rows))

    # ↓↓↓ ここに実際の加工処理を書く（絞り込み・突合・集計など） ↓↓↓

    # ↑↑↑ ここまで ↑↑↑

    output_path = config.REPORT.OUTPUT_FOLDER / FileNameBuilder(BATCH_NAME).prefix()
    with ExcelFile.create(output_path) as f:
        s = f.sheet(SHEET)
        s.write_table(rows)
        s.auto_width()
        s.freeze_header()
        f.save()
    logger.info("出力: %s", output_path)

    notify(f"{BATCH_NAME} 完了", body=f"{len(rows)} 件を処理しました\n出力: {output_path}")


if __name__ == "__main__":
    setup_logger("main")
    # 動きを確認したいだけのとき: from comken import set_dry_run; set_dry_run(True)
    # （ファイル出力・Teams 送信をスキップして、流れだけ [DRY-RUN] ログで確認できる）
    try:
        main()
    except OriginalLibsError as e:
        # comken のエラーはメッセージに対処法が入っている → そのまま通知して調査の起点にする
        logger.error("処理を中断しました: %s", e)
        notify(f"{BATCH_NAME} エラー", body=str(e), color=CardColor.RED)
        raise
    except Exception as e:
        logger.error("予期しないエラーが発生しました", exc_info=True)
        notify(f"{BATCH_NAME} エラー", body=str(e), color=CardColor.RED)
        raise
