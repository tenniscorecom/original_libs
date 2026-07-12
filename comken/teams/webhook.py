"""
teams/webhook.py — Microsoft Teams 通知（Power Automate Webhook）

Power Automate（ワークフロー）の Webhook 経由で Teams チャンネルにメッセージを送る。
requests 等の外部ライブラリは不要（Python 標準ライブラリのみ）。

送信形式は Adaptive Card なので、旧来の Incoming Webhook（コネクタ）でも動く。

事前設定（チャンネルごとに1回だけ）:
    Teams チャンネル → 「…」メニュー → ワークフロー
    → 「Webhook 要求を受信したらチャネルに投稿する」テンプレート → URL をコピー

使い方:
    from comken.teams import CardColor, TeamsNotifier

    notifier = TeamsNotifier("https://prod-xx.japaneast.logic.azure.com/workflows/...")

    # テキストだけ
    notifier.send("処理が完了しました")

    # タイトル + 本文（カード形式）
    notifier.send_card("売上集計 完了", body="3,421 件を処理しました")

    # エラー通知（タイトルが赤くなる）
    notifier.send_card("エラーが発生しました", body=str(e), color=CardColor.RED)
"""

import json
import urllib.error
import urllib.request

from ..exceptions import TeamsError


class CardColor:
    """send_card の color 引数に使う定数（Adaptive Card の色名）。"""

    DEFAULT = "Default"
    BLUE = "Accent"
    GREEN = "Good"
    ORANGE = "Warning"
    RED = "Attention"


class TeamsNotifier:
    """Teams チャンネルへの通知クライアント（Power Automate Webhook）。

    使い方:
        notifier = TeamsNotifier(webhook_url)
        notifier.send("処理が完了しました")
        notifier.send_card("売上集計 完了", body="3,421 件を処理しました")
        notifier.send_card("エラー", body=str(e), color=CardColor.RED)
    """

    TIMEOUT = 30

    def __init__(self, webhook_url: str) -> None:
        """
        Args:
            webhook_url: Power Automate の Webhook URL。
                         チャンネル → ワークフロー →
                         「Webhook 要求を受信したらチャネルに投稿する」から取得する。
        """
        self._url = webhook_url

    def send(self, text: str) -> None:
        """テキストメッセージを送る。

        Args:
            text: 送信するメッセージ。Markdown 記法が使える（太字: **text**）。
        """
        self._post(self._build_card([self._text_block(text)]))

    def send_card(self, title: str, body: str = "", color: str = CardColor.DEFAULT) -> None:
        """タイトルと本文付きのカード形式メッセージを送る。

        Args:
            title: カードのタイトル（太字・大きめで表示される）。
            body: カードの本文（省略可）。
            color: タイトルの色（CardColor 定数。デフォルト: CardColor.DEFAULT）。
                   エラー通知なら CardColor.RED、警告なら CardColor.ORANGE など。
        """
        blocks = [
            {
                "type": "TextBlock",
                "text": title,
                "weight": "Bolder",
                "size": "Medium",
                "color": color,
                "wrap": True,
            }
        ]
        if body:
            blocks.append(self._text_block(body))
        self._post(self._build_card(blocks))

    @staticmethod
    def _text_block(text: str) -> dict:
        return {"type": "TextBlock", "text": text, "wrap": True}

    @staticmethod
    def _build_card(blocks: list[dict]) -> dict:
        """Adaptive Card 形式のペイロードを組み立てる。"""
        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "msteams": {"width": "Full"},
                        "body": blocks,
                    },
                }
            ],
        }

    def _post(self, payload: dict) -> None:
        """ペイロードを POST する。

        Raises:
            TeamsError: HTTP エラー、またはネットワークに接続できない場合。
        """
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self._url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                resp.read()
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise TeamsError(TeamsError.MSG_HTTP.format(code=e.code, detail=detail)) from e
        except urllib.error.URLError as e:
            raise TeamsError(TeamsError.MSG_CONNECTION.format(reason=e.reason)) from e
