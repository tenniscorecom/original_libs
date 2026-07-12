"""
teams/webhook.py — Microsoft Teams Incoming Webhook 通知

Microsoft 365 の Teams チャンネルに Incoming Webhook 経由でメッセージを送る。
requests 等の外部ライブラリは不要（Python 標準ライブラリのみ）。

事前設定:
    Teams チャンネル → ‥ メニュー → コネクタ → Incoming Webhook → 追加 → URL をコピー

使い方:
    from comken.teams import TeamsNotifier

    notifier = TeamsNotifier("https://xxx.webhook.office.com/webhookb2/...")

    # テキストだけ
    notifier.send("処理が完了しました")

    # タイトル + 本文（カード形式）
    notifier.send_card("売上集計 完了", body="3,421 件を処理しました")

    # エラー通知（赤い帯）
    notifier.send_card("エラーが発生しました", body=str(e), color="FF0000")
"""

import json
import urllib.request


class TeamsNotifier:
    """Teams チャンネルへの通知クライアント。

    使い方:
        notifier = TeamsNotifier(webhook_url)
        notifier.send("処理が完了しました")
        notifier.send_card("売上集計 完了", body="3,421 件を処理しました")
    """

    TIMEOUT = 30

    def __init__(self, webhook_url: str) -> None:
        """
        Args:
            webhook_url: Teams の Incoming Webhook URL。
                         チャンネル → コネクタ → Incoming Webhook から取得する。
        """
        self._url = webhook_url

    def send(self, text: str) -> None:
        """テキストメッセージを送る。

        Args:
            text: 送信するメッセージ。Markdown 記法が使える（太字: **text**、改行: \\n\\n）。
        """
        self._post({"text": text})

    def send_card(self, title: str, body: str = "", color: str = "0076D7") -> None:
        """タイトルと本文付きのカード形式メッセージを送る。

        Args:
            title: カードのタイトル（太字で表示される）。
            body: カードの本文（省略可）。
            color: 左側の帯の色（16進数 RGB、デフォルト: 青 "0076D7"）。
                   エラー通知なら "FF0000"（赤）、警告なら "FFA500"（オレンジ）など。
        """
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": title,
            "sections": [
                {
                    "activityTitle": title,
                    "activityText": body,
                }
            ],
        }
        self._post(payload)

    def _post(self, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self._url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
            resp.read()
